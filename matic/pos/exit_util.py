from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import rlp

from matic import services
from matic.abstracts import BaseWeb3Client
from matic.constants import LogEventSignature
from matic.exceptions import BurnTxNotCheckPointedException, ProofAPINotSetException
from matic.json_types import IBaseClientConfig, IRootBlockInfo, ITransactionReceipt
from matic.pos.root_chain import RootChain
from matic.utils import to_hex
from matic.utils.proof_utils import ProofUtil
from matic.utils.web3_side_chain_client import Web3SideChainClient

# import { RootChain } from "./root_chain"
# import { Converter, ProofUtil, Web3SideChainClient } from "../utils"
# import { bufferToHex, rlp } from "ethereumjs-util"
# import { IBlockWithTransaction, ITransactionReceipt } from "../interfaces"
# import { service } from "../services"
# import { BaseBigNumber, BaseWeb3Client } from "../abstracts"
# import { ErrorHelper } from "../utils/error_helper"
# import { ERROR_TYPE, IBaseClientConfig, IRootBlockInfo, utils } from ".."

# FIXME: wtf is that?
HASHES_1: Final = {
    LogEventSignature.ERC_721_TRANSFER,
    LogEventSignature.ERC_721_TRANSFER_WITH_METADATA,
}
HASHES_2: Final = {
    LogEventSignature.ERC_1155_TRANSFER,
    LogEventSignature.ERC_1155_BATCH_TRANSFER,
}
SIG_3: Final = '0xf871896b17e9cb7a64941c62c188a4f5c621b86800e3d15452ece01ce56073df'
ZERO_SIG: Final = '0x0000000000000000000000000000000000000000000000000000000000000000'


@dataclass
class IChainBlockInfo:
    last_child_block: str
    tx_block_number: int


class ExitUtil:
    _matic_client: BaseWeb3Client

    root_chain: RootChain

    request_concurrency: Final = 0  # FIXME: remove
    config: IBaseClientConfig

    def __init__(self, client: Web3SideChainClient, root_chain: RootChain):
        self._matic_client = client.child
        self.root_chain = root_chain
        self.config = client.config

    def _get_log_index(self, log_event_sig: bytes, receipt: ITransactionReceipt) -> int:
        log_index = None

        if log_event_sig in HASHES_1:
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
        elif log_event_sig in HASHES_2:
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
        if log_event_sig in HASHES_1:
            log_indices = [
                i
                for i, log in enumerate(receipt.logs)
                if (
                    len(log.topics) >= 2
                    and log.topics[0].lower() == log_event_sig.lower()
                    and log.topics[2].lower() == ZERO_SIG
                )
            ]
        elif log_event_sig in HASHES_2:
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

    def get_chain_block_info(self, burn_tx_hash: bytes) -> IChainBlockInfo:
        tx_block = self._matic_client.get_transaction(burn_tx_hash).block_number
        assert tx_block is not None

        return IChainBlockInfo(
            last_child_block=self.root_chain.last_child_block,
            tx_block_number=tx_block,
        )

    def _is_checkpointed(self, data: IChainBlockInfo) -> bool:
        # lastchild block is greater equal to transacton block int
        return int(data.last_child_block) >= int(data.tx_block_number)

    def is_checkpointed(self, burn_tx_hash: bytes) -> bool:
        return self._is_checkpointed(self.get_chain_block_info(burn_tx_hash))

    def _get_root_block_info(self, tx_block_number: int) -> IRootBlockInfo:
        """Returns info about block int existence on parent chain.

        1. root block int,
        2. start block int,
        3. end block int

        :param tx_block_number: Transaction block int on child chain
        :returns IRootBlockInfo:
        """
        # find in which block child was included in parent
        root_block_number: int

        block_number = self.root_chain.find_root_block_from_child(tx_block_number)
        root_block_number = block_number

        root_block_info = self.root_chain.method(
            'headerBlocks',
            to_hex(block_number),
        ).read()

        return IRootBlockInfo(
            header_block_number=root_block_number,
            end=root_block_info.end,
            start=root_block_info.start,
        )

    def _get_root_block_info_from_api(self, tx_block_number: int):
        self._matic_client.logger.debug('block info from API 1')

        try:
            header_block = services.get_block_included(
                self.config.network, tx_block_number
            )
            self._matic_client.logger.debug('block info from API 2', header_block)

            if not (
                header_block
                and header_block.start
                and header_block.end
                and header_block.header_block_number
            ):
                raise ValueError('Network API Error')
            return header_block
        except Exception as e:
            self._matic_client.logger.debug('Block info from API error: ', e)
            return self._get_root_block_info(tx_block_number)

    def _get_block_proof(self, tx_block_number: int, root_block_info: Any):
        # FIXME: root_block_info -> start + end or -> _AnyWithStartEnd (worseee)
        return ProofUtil.build_block_proof(
            self._matic_client,
            int(root_block_info.start),
            int(root_block_info.end),
            tx_block_number,
        )

    def _get_block_proof_from_api(self, tx_block_number: int, root_block_info: Any):
        try:
            block_proof = services.get_proof(
                self.config.network,
                root_block_info.start,
                root_block_info.end,
                tx_block_number,
            )
            if not block_proof:
                raise RuntimeError('Network API Error')

            self._matic_client.logger.debug('block proof from API 1')
            return block_proof
        except Exception as e:
            self._matic_client.logger.debug('API error: ', e)
            return self._get_block_proof(tx_block_number, root_block_info)

    def build_payload_for_exit(
        self, burn_tx_hash: bytes, index: int, log_event_sig: bytes, is_fast: bool
    ):
        if is_fast and not services:
            raise ProofAPINotSetException

        if index < 0:
            raise ValueError('Index must not be a negative integer')

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
            root_block_info_result = self._get_root_block_info_from_api(tx_block_number)
        else:
            root_block_info_result = self._get_root_block_info(tx_block_number)

        root_block_info = root_block_info_result
        # step 4 - build block proof
        if is_fast:
            block_proof_result = self._get_block_proof_from_api(
                tx_block_number, root_block_info
            )
        else:
            block_proof_result = self._get_block_proof(tx_block_number, root_block_info)

        block_proof = block_proof_result
        # step 5- create receipt proof
        receipt_proof = ProofUtil.get_receipt_proof(
            receipt, block, self._matic_client, self.request_concurrency
        )

        # step 6 - encode payload, convert into hex
        if index > 0:
            log_indices = self._get_all_log_indices(log_event_sig, receipt)
            if index >= len(log_indices):
                raise ValueError(
                    'Index is grater than the int of tokens in self transaction'
                )

            return self._encode_payload(
                root_block_info.header_block_number.toNumber(),
                block_proof,
                tx_block_number,
                block.timestamp,
                block.transactions_root[2:],
                block.receipts_root[2:],
                ProofUtil.get_receipt_bytes(receipt),  # rlp encoded
                receipt_proof.parentNodes,
                receipt_proof.path,
                log_indices[index],
            )
        else:
            log_index = self._get_log_index(log_event_sig, receipt)

            return self._encode_payload(
                root_block_info.header_block_number.toNumber(),
                block_proof,
                tx_block_number,
                block.timestamp,
                block.transactions_root[2:],
                block.receipts_root[2:],
                ProofUtil.get_receipt_bytes(receipt),  # rlp encoded
                receipt_proof.parentNodes,
                receipt_proof.path,
                log_index,
            )

    def build_multiple_payloads_for_exit(
        self, burn_tx_hash: bytes, log_event_sig: bytes, is_fast: bool
    ):
        if is_fast and not services.DEFAULT_PROOF_API_URL:  # NOTSURE
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
            root_block_info_result = self._get_root_block_info_from_api(tx_block_number)
        else:
            root_block_info_result = self._get_root_block_info(tx_block_number)

        root_block_info = root_block_info_result
        # step 4 - build block proof
        if is_fast:
            block_proof_result = self._get_block_proof_from_api(
                tx_block_number, root_block_info
            )
        else:
            block_proof_result = self._get_block_proof(tx_block_number, root_block_info)

        block_proof = block_proof_result
        # step 5- create receipt proof
        receipt_proof = ProofUtil.get_receipt_proof(
            receipt, block, self._matic_client, self.request_concurrency
        )
        log_indices = self._get_all_log_indices(log_event_sig, receipt)

        # step 6 - encode payloads, convert into hex
        return [
            self._encode_payload(
                root_block_info.header_block_number,
                block_proof,
                tx_block_number,
                block.timestamp,
                block.transactions_root,
                block.receipts_root,
                ProofUtil.get_receipt_bytes(receipt),  # rlp encoded
                receipt_proof.parentNodes,
                receipt_proof.path,
                log_index,
            )
            for log_index in log_indices
        ]

    def _encode_payload(
        self,
        header_number,
        build_block_proof,
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
                build_block_proof,
                block_number,
                timestamp,
                transactions_root,
                receipts_root,
                receipt,
                rlp.encode(receipt_parent_nodes),
                b''.join([bytes(1), path]),  # NOTSURE
                log_index,
            ]
        )

    def get_exit_hash(self, burn_tx_hash, index, log_event_sig) -> bytes:
        last_child_block = self.root_chain.last_child_block
        receipt = self._matic_client.get_transaction_receipt(burn_tx_hash)
        block_result = self._matic_client.get_block_with_transaction(
            receipt.block_number
        )
        block = block_result
        if not self._is_checkpointed(
            IChainBlockInfo(
                last_child_block=last_child_block, tx_block_number=receipt.block_number
            )
        ):
            raise BurnTxNotCheckPointedException()

        receipt_proof = ProofUtil.get_receipt_proof(
            receipt, block, self._matic_client, self.request_concurrency
        )

        log_index = None
        nibble = b''.join(
            b''.join(
                (
                    (byte // 0x10).to_bytes(1, 'big'),
                    (byte % 0x10).to_bytes(1, 'big'),
                )
            )
            for byte in receipt_proof.path
        )

        if index > 0:
            log_indices = self._get_all_log_indices(log_event_sig, receipt)
            log_index = log_indices[index]

        log_index = self._get_log_index(log_event_sig, receipt)

        return self._matic_client.etherium_sha3(receipt.block_number, nibble, log_index)
