from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final

import rlp

from matic import services
from matic.abstracts import BaseWeb3Client
from matic.constants import LogEventSignature
from matic.exceptions import BurnTxNotCheckPointedException, ProofAPINotSetException
from matic.json_types import IBaseClientConfig, IRootBlockInfo, ITransactionReceipt
from matic.pos.root_chain import RootChain
from matic.utils import proof_utils
from matic.utils.web3_side_chain_client import Web3SideChainClient

ERC_721_HASHES: Final = {
    LogEventSignature.ERC_721_TRANSFER,
    LogEventSignature.ERC_721_TRANSFER_WITH_METADATA,
}
ERC_1155_HASHES: Final = {
    LogEventSignature.ERC_1155_TRANSFER,
    LogEventSignature.ERC_1155_BATCH_TRANSFER,
}
ZERO_SIG: Final = bytes(32)


@dataclass
class _IChainBlockInfo:
    """Internal dataclass."""

    last_child_block: int
    tx_block_number: int


class ExitUtil:
    """Helper utility class for building and performing exit actions with POS bridge."""

    _matic_client: BaseWeb3Client
    root_chain: RootChain
    config: IBaseClientConfig

    def __init__(self, client: Web3SideChainClient, root_chain: RootChain):
        self._matic_client = client.child
        self.root_chain = root_chain
        self.config = client.config

    def _get_log_index(self, log_event_sig: bytes, receipt: ITransactionReceipt) -> int:
        log_index = None

        if log_event_sig in ERC_721_HASHES:
            log_index = next(
                (
                    i
                    for i, log in enumerate(receipt.logs)
                    if (
                        len(log.topics) >= 2
                        and log.topics[0].lower() == log_event_sig.lower()
                        and log.topics[2].lower() == ZERO_SIG
                    )
                ),
                None,
            )
        elif log_event_sig in ERC_1155_HASHES:
            log_index = next(
                (
                    i
                    for i, log in enumerate(receipt.logs)
                    if (
                        len(log.topics) >= 3
                        and log.topics[0].lower() == log_event_sig.lower()
                        and log.topics[3].lower() == ZERO_SIG
                    )
                ),
                None,
            )
        else:
            log_index = next(
                (
                    i
                    for i, log in enumerate(receipt.logs)
                    if (log.topics and log.topics[0].lower() == log_event_sig.lower())
                ),
                None,
            )

        if log_index is None:
            raise ValueError('Log not found in receipt')
        return log_index

    def _get_all_log_indices(
        self, log_event_sig: bytes, receipt: ITransactionReceipt
    ) -> list[int]:
        if log_event_sig in ERC_721_HASHES:
            log_indices = [
                i
                for i, log in enumerate(receipt.logs)
                if (
                    len(log.topics) >= 2
                    and log.topics[0].lower() == log_event_sig.lower()
                    and log.topics[2].lower() == ZERO_SIG
                )
            ]
        elif log_event_sig in ERC_1155_HASHES:
            log_indices = [
                i
                for i, log in enumerate(receipt.logs)
                if (
                    len(log.topics) >= 3
                    and log.topics[0].lower() == log_event_sig.lower()
                    and log.topics[3].lower() == ZERO_SIG
                )
            ]
        elif log_event_sig == LogEventSignature.ERC_721_BATCH_TRANSFER:
            log_indices = [
                i
                for i, log in enumerate(receipt.logs)
                if (
                    len(log.topics) >= 2
                    and log.topics[0].lower() == LogEventSignature.ERC_20_TRANSFER
                    and log.topics[2].lower() == ZERO_SIG
                )
            ]
        else:
            log_indices = [
                i
                for i, log in enumerate(receipt.logs)
                if log.topics and log.topics[0].lower() == log_event_sig.lower()
            ]

        if not log_indices:
            raise ValueError('Log not found in receipt')

        return log_indices

    def get_chain_block_info(self, burn_tx_hash: bytes) -> _IChainBlockInfo:
        """Obtain information about block that includes given transaction."""
        tx = self._matic_client.get_transaction(burn_tx_hash)
        tx_block = tx.block_number
        assert tx_block is not None

        return _IChainBlockInfo(
            last_child_block=self.root_chain.last_child_block,
            tx_block_number=tx_block,
        )

    def _is_checkpointed(self, data: _IChainBlockInfo) -> bool:
        return int(data.last_child_block) >= int(data.tx_block_number)

    def is_checkpointed(self, burn_tx_hash: bytes) -> bool:
        """Check if given transaction is checkpointed."""
        return self._is_checkpointed(self.get_chain_block_info(burn_tx_hash))

    def _get_root_block_info(self, tx_block_number: int) -> IRootBlockInfo:
        """Returns info about block int existence on parent chain."""
        # find in which block child was included in parent
        block_number = self.root_chain.find_root_block_from_child(tx_block_number)
        _, start, end, _, _ = self.root_chain.method(
            'headerBlocks', block_number
        ).read()

        return IRootBlockInfo(
            header_block_number=block_number,
            start=start,
            end=end,
        )

    def _get_root_block_info_from_api(self, tx_block_number: int) -> IRootBlockInfo:
        try:
            header_block = services.get_block_included(
                self.config['network'], tx_block_number
            )
            self._matic_client.logger.debug('block info from API %s', header_block)

            if not (
                header_block
                and header_block.start
                and header_block.end
                and header_block.header_block_number
            ):
                raise ValueError('Network API Error')
            return header_block
        except Exception as e:  # noqa
            self._matic_client.logger.error('Block info from API error: %r', e)
            return self._get_root_block_info(tx_block_number)

    def _get_block_proof(
        self, tx_block_number: int, root_block_info: IRootBlockInfo
    ) -> bytes:
        return proof_utils.build_block_proof(
            self._matic_client,
            int(root_block_info.start),
            int(root_block_info.end),
            tx_block_number,
        )

    def _get_block_proof_from_api(
        self, tx_block_number: int, root_block_info: IRootBlockInfo
    ) -> bytes:
        try:
            block_proof = services.get_proof(
                self.config['network'],
                root_block_info.start,
                root_block_info.end,
                tx_block_number,
            )
            if not block_proof:
                raise RuntimeError('Network API Error')

            self._matic_client.logger.debug('block proof from API 1')
            return block_proof
        except ProofAPINotSetException:
            raise
        except Exception as e:  # noqa
            self._matic_client.logger.error('API error: %r', e)
            return self._get_block_proof(tx_block_number, root_block_info)

    def build_payload_for_exit(
        self, burn_tx_hash: bytes, index: int, log_event_sig: bytes, is_fast: bool
    ) -> bytes:
        """Build exit payload for transaction hash."""
        if index < 0:
            raise ValueError('Index must not be a negative integer')

        def get_indices(
            log_event_sig: bytes, receipt: ITransactionReceipt
        ) -> list[int]:
            if index > 0:
                log_indices = self._get_all_log_indices(log_event_sig, receipt)
                if index >= len(log_indices):
                    raise ValueError(
                        'Index is greater than the number of tokens in this transaction'
                    )
                return [log_indices[index]]
            else:
                return [self._get_log_index(log_event_sig, receipt)]

        return self._build_multiple_payloads_for_exit(
            burn_tx_hash, log_event_sig, is_fast, get_indices
        )[0]

    def build_multiple_payloads_for_exit(
        self, burn_tx_hash: bytes, log_event_sig: bytes, is_fast: bool
    ) -> list[bytes]:
        """Build exit payload for multiple indices."""
        return self._build_multiple_payloads_for_exit(
            burn_tx_hash, log_event_sig, is_fast, self._get_all_log_indices
        )

    def _build_multiple_payloads_for_exit(
        self,
        burn_tx_hash: bytes,
        log_event_sig: bytes,
        is_fast: bool,
        get_indices: Callable[[bytes, ITransactionReceipt], list[int]],
    ) -> list[bytes]:
        if is_fast and not services.DEFAULT_PROOF_API_URL:
            raise ProofAPINotSetException

        block_info = self.get_chain_block_info(burn_tx_hash)

        if not self._is_checkpointed(block_info):
            raise ValueError('Burn transaction has not been checkpointed as yet')

        # step 1 - Get Block int from transaction hash
        tx_block_number = block_info.tx_block_number

        # step 2-  get transaction receipt from txhash and
        # block information from block int
        receipt = self._matic_client.get_transaction_receipt(burn_tx_hash)
        block = self._matic_client.get_block_with_transaction(tx_block_number)

        # step  3 - get information about block saved in parent chain
        if is_fast:
            root_block_info = self._get_root_block_info_from_api(tx_block_number)
        else:
            root_block_info = self._get_root_block_info(tx_block_number)

        # step 4 - build block proof
        if is_fast:
            block_proof = self._get_block_proof_from_api(
                tx_block_number, root_block_info
            )
        else:
            block_proof = self._get_block_proof(tx_block_number, root_block_info)

        # step 5- create receipt proof
        receipt_proof = proof_utils.get_receipt_proof(
            receipt, block, self._matic_client
        )
        log_indices = get_indices(log_event_sig, receipt)

        # step 6 - encode payloads, convert into hex
        return [
            self._encode_payload(
                root_block_info.header_block_number,
                block_proof,
                tx_block_number,
                block.timestamp,
                block.transactions_root,
                block.receipts_root,
                proof_utils.get_receipt_bytes(receipt),  # rlp encoded
                receipt_proof['parent_nodes'],
                receipt_proof['path'],
                log_index,
            )
            for log_index in log_indices
        ]

    def _encode_payload(
        self,
        header_number,
        block_proof: bytes,
        block_number,
        timestamp,
        transactions_root,
        receipts_root,
        receipt,
        receipt_parent_nodes,
        path,
        log_index,
    ) -> bytes:
        return rlp.encode(
            [
                header_number,
                block_proof,
                block_number,
                timestamp,
                transactions_root,
                receipts_root,
                receipt,
                rlp.encode(receipt_parent_nodes),
                b'\x00' + path,
                log_index,
            ]
        )

    def get_exit_hash(
        self, burn_tx_hash: bytes, index: int, log_event_sig: bytes
    ) -> bytes:
        """Build exit hash for burn transaction."""
        last_child_block = self.root_chain.last_child_block
        receipt = self._matic_client.get_transaction_receipt(burn_tx_hash)
        block_result = self._matic_client.get_block_with_transaction(
            receipt.block_number
        )
        block = block_result
        if not self._is_checkpointed(
            _IChainBlockInfo(
                last_child_block=last_child_block, tx_block_number=receipt.block_number
            )
        ):
            raise BurnTxNotCheckPointedException()

        receipt_proof = proof_utils.get_receipt_proof(
            receipt, block, self._matic_client
        )

        log_index = None
        nibble = b''.join(
            b''.join(
                (
                    (byte // 0x10).to_bytes(1, 'big'),
                    (byte % 0x10).to_bytes(1, 'big'),
                )
            )
            for byte in receipt_proof['path']
        )

        if index > 0:
            log_indices = self._get_all_log_indices(log_event_sig, receipt)
            log_index = log_indices[index]

        log_index = self._get_log_index(log_event_sig, receipt)

        return self._matic_client.etherium_sha3(
            ['uint256', 'bytes', 'uint256'],
            [receipt.block_number, nibble, log_index],
        )
