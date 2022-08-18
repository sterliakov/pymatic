from __future__ import annotations

from typing import Sequence

from matic.constants import LogEventSignature
from matic.json_types import IExitTransactionOption, ITransactionOption
from matic.pos.pos_token import TokenWithApproveAll


class ERC721(TokenWithApproveAll):
    CONTRACT_NAME: str = 'ChildERC721'
    BURN_EVENT_SIGNATURE_SINGLE: bytes = LogEventSignature.ERC_721_TRANSFER

    @staticmethod
    def _validate_many(token_ids: Sequence[int]) -> list[int]:
        """Assert sequence length is less than 20."""
        if len(token_ids) > 20:
            raise ValueError('can not process more than 20 tokens')

        return list(token_ids)

    def get_tokens_count(
        self, user_address: str, options: ITransactionOption | None = None
    ) -> int:
        """Get tokens count for the user."""
        method = self.contract.method('balanceOf', user_address)
        return int(self.process_read(method, options))

    def get_token_id_at_index_for_user(
        self, index: int, user_address: str, options: ITransactionOption | None = None
    ) -> int:
        """Get token id on supplied index for user."""
        method = self.contract.method('tokenOfOwnerByIndex', user_address, index)

        return int(self.process_read(method, options))

    def get_all_tokens(self, user_address: str, limit: int | None = None) -> list[int]:
        """Get all tokens for user."""
        count = self.get_tokens_count(user_address)
        if limit is not None and count > limit:
            count = limit

        # TODO: should be async
        return [
            self.get_token_id_at_index_for_user(i, user_address) for i in range(count)
        ]

    def is_approved(
        self, token_id: int, option: ITransactionOption | None = None
    ) -> bool:
        """Check if given token is approved for contract."""
        self.check_for_root()

        method = self.contract.method('getApproved', token_id)
        return self.predicate_address == self.process_read(method, option)

    def approve(
        self, token_id: int, private_key: str, option: ITransactionOption | None = None
    ):
        self.check_for_root()

        method = self.contract.method('approve', self.predicate_address, token_id)
        return self.process_write(method, option, private_key)

    def deposit(
        self,
        token_id: int,
        user_address: str,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        amount_in_abi = self.client.parent.encode_parameters([token_id], ['uint256'])
        return self.root_chain_manager.deposit(
            user_address,
            self.contract_param.address,
            amount_in_abi,
            private_key,
            option,
        )

    def deposit_many(
        self,
        token_ids: Sequence[int],
        user_address: str,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        self._validate_many(token_ids)
        amount_in_abi = self.client.parent.encode_parameters([token_ids], ['uint256[]'])
        return self.root_chain_manager.deposit(
            user_address,
            self.contract_param.address,
            amount_in_abi,
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

        self._validate_many(token_ids)
        method = self.contract.method('withdrawBatch', token_ids)
        return self.process_write(method, option, private_key)

    def withdraw_exit_on_index(
        self,
        burn_transaction_hash: bytes,
        index: int,
        private_key: str,
        option: IExitTransactionOption | None = None,
    ):
        """Complete withdraw process for token on given index.

        This function should be called after checkpoint has been submitted
        for the block containing burn tx.

        This function uses API to fetch proof data.
        """
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            self.BURN_EVENT_SIGNATURE,
            private_key,
            True,
            index,
            option=option,
        )

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
        from_: str,
        to: str,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Transfer to another user."""
        return self.transfer_erc_721(from_, to, token_id, private_key, option)
