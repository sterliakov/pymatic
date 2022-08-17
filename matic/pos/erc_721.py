from __future__ import annotations

from typing import Sequence

from matic.constants import LogEventSignature
from matic.json_types import ITransactionOption
from matic.pos.pos_token import POSToken

# from matic.utils import to_hex

# import { IPOSClientConfig, IPOSContracts, ITransactionOption } from "../interfaces"
# import { RootChainManager } from "./root_chain_manager"
# import { Converter, Web3SideChainClient } from "../utils"
# import { POSToken } from "./pos_token"
# import { int } from "../types"
# import { ExitUtil } from "./exit_util"
# import { LogEventSignature } from "../enums"


class ERC721(POSToken):
    CONTRACT_NAME: str = 'ChildERC721'

    def _validate_many(self, token_ids: Sequence[int]) -> list[int]:
        """Convert to hex.

        FIXME: Why like this, very odd
        """
        if len(token_ids) > 20:
            # FIXME: wtf?
            raise ValueError('can not process more than 20 tokens')

        return list(token_ids)

    def get_tokens_count(
        self, user_address: bytes, options: ITransactionOption | None = None
    ):
        """Get tokens count for the user."""
        method = self.contract.method('balanceOf', user_address)
        return int(self.process_read(method, options))

    def get_token_id_at_index_for_user(
        self, index: int, user_address: bytes, options: ITransactionOption | None = None
    ):
        """Get token id on supplied index for user."""
        method = self.contract.method('tokenOfOwnerByIndex', user_address, index)

        return int(self.process_read(method, options))

    def get_all_tokens(self, user_address: bytes, limit: int | None = None):
        """Get all tokens for user."""
        count = self.get_tokens_count(user_address)
        if limit is not None and count > limit:
            count = limit

        # TODO: should be async
        return [
            self.get_token_id_at_index_for_user(i, user_address) for i in range(count)
        ]

    def is_approved(self, token_id: int, option: ITransactionOption | None = None):
        self.check_for_root()

        method = self.contract.method('getApproved', token_id)
        return self.predicate_address == self.process_read(method, option)

    def is_approved_all(
        self, user_address: bytes, option: ITransactionOption | None = None
    ):
        self.check_for_root()

        method = self.contract.method(
            'isApprovedForAll', user_address, self.predicate_address
        )
        return bool(self.process_read(method, option))

    def approve(
        self, token_id: int, private_key: str, option: ITransactionOption | None = None
    ):
        self.check_for_root()

        method = self.contract.method('approve', self.predicate_address, token_id)
        return self.process_write(method, option, private_key)

    def approve_all(self, private_key: str, option: ITransactionOption | None = None):
        self.check_for_root()

        method = self.contract.method('setApprovalForAll', self.predicate_address, True)
        return self.process_write(method, option, private_key)

    def deposit(
        self,
        token_id: int,
        user_address: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        amount_in_ABI = self.client.parent.encode_parameters([token_id], ['uint256'])
        return self.root_chain_manager.deposit(
            user_address,
            self.contract_param.address,
            amount_in_ABI,
            private_key,
            option,
        )

    def deposit_many(
        self,
        token_ids: Sequence[int],
        user_address: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        tokens_in_hex = self._validate_many(token_ids)
        amount_in_ABI = self.client.parent.encode_parameters(
            [tokens_in_hex], ['uint256[]']
        )
        return self.root_chain_manager.deposit(
            user_address,
            self.contract_param.address,
            amount_in_ABI,
            private_key,
            option,
        )

    def withdraw_start(
        self, token_id: int, private_key: str, option: ITransactionOption | None = None
    ):
        self.check_for_child()

        method = self.contract.method('withdraw', token_id)
        return self.process_write(method, option, private_key)

    def withdraw_start_with_metadata(
        self, token_id: int, private_key: str, option: ITransactionOption | None = None
    ):
        self.check_for_child()

        method = self.contract.method('withdrawWithMetadata', token_id)
        return self.process_write(method, option, private_key)

    def withdraw_start_many(
        self,
        token_ids: Sequence[int],
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_child()

        tokens_in_hex = self._validate_many(token_ids)
        method = self.contract.method('withdrawBatch', tokens_in_hex)
        return self.process_write(method, option, private_key)

    def withdraw_exit(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        self.check_for_root()

        payload = self.exit_util.build_payload_for_exit(
            burn_transaction_hash, 0, LogEventSignature.ERC_721_TRANSFER, False
        )
        return self.root_chain_manager.exit(payload, option)

    def withdraw_exit_on_index(
        self,
        burn_transaction_hash: bytes,
        index: int,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        payload = self.exit_util.build_payload_for_exit(
            burn_transaction_hash, index, LogEventSignature.ERC_721_TRANSFER, False
        )
        return self.root_chain_manager.exit(payload, option)

    # // async withdrawExitMany(burn_transaction_hash: bytes, option: ITransactionOption | None = None) {
    # //     self.check_for_root()

    # //     return self.exit_util.buildMultiplePayloadsForExit(
    # //         burn_transaction_hash,
    # //         LogEventSignature.ERC_721_BATCH_TRANSFER,
    # //         False
    # //     ).then(async payloads => {
    # //         const exitTxs = []
    # //         if()
    # //         for(const i in payloads) {
    # //           exitTxs.push(self.root_chain_manager.exit(
    # //             payloads[i], option
    # //         ))
    # //         }
    # //         return Promise.all(exitTxs)
    # //         })
    # // }

    def withdraw_exit_faster(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        self.check_for_root()

        payload = self.exit_util.build_payload_for_exit(
            burn_transaction_hash, 0, LogEventSignature.ERC_721_TRANSFER, True
        )
        return self.root_chain_manager.exit(payload, option)

    # // withdrawExitFasterMany(burn_transaction_hash: bytes, option: ITransactionOption | None = None) {
    # //     self.check_for_root()

    # //     return self.exit_util.build_payload_for_exit(
    # //         burn_transaction_hash,
    # //         LogEventSignature.ERC_721_BATCH_TRANSFER,
    # //         True
    # //     ).then(payload => {
    # //         return self.root_chain_manager.exit(
    # //             payload, option
    # //         )
    # //     })
    # // }

    def is_withdraw_exited(self, tx_hash: bytes) -> bool:
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_721_TRANSFER)

    def is_withdraw_exited_many(self, tx_hash: bytes) -> bool:
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_721_BATCH_TRANSFER)

    def is_withdraw_exited_on_index(self, tx_hash: bytes, index: int) -> bool:
        return self.is_withdrawn_on_index(
            tx_hash, index, LogEventSignature.ERC_721_TRANSFER
        )

    def transfer(
        self,
        token_id: int,
        from_: bytes,
        to: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Transfer to another user."""
        return self.transfer_ERC_721(from_, to, token_id, private_key, option)
