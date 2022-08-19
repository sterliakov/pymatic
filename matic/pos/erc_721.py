from __future__ import annotations

from typing import Sequence

from matic.constants import LogEventSignature
from matic.json_types import IExitTransactionOption, ITransactionOption
from matic.pos.pos_token import TokenWithApproveAll


class ERC721(TokenWithApproveAll):
    """Arbitrary ERC-721-compliant token."""

    CONTRACT_NAME: str = 'ChildERC721'
    BURN_EVENT_SIGNATURE: bytes = LogEventSignature.ERC_721_TRANSFER

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
        method = self.method('balanceOf', user_address)
        return int(self.process_read(method, options))

    def get_token_id_at_index_for_user(
        self, index: int, user_address: str, options: ITransactionOption | None = None
    ) -> int:
        """Get token id on supplied index for user."""
        method = self.method('tokenOfOwnerByIndex', user_address, index)

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
        method = self.method('getApproved', token_id)
        return self.predicate_address == self.process_read(method, option)

    def approve(
        self,
        token_id: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Approve token with given id to contract (root chain)."""
        self.check_for_root()
        method = self.method('approve', self.predicate_address, token_id)
        return self.process_write(method, option, private_key)

    def deposit(
        self,
        token_id: int,
        user_address: str,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Deposit given token from root chain to child."""
        self.check_for_root()
        amount_in_abi = self.client.parent.encode_parameters([token_id], ['uint256'])
        return self.root_chain_manager.deposit(
            user_address,
            self.address,
            amount_in_abi,
            private_key,
            option,
        )

    def deposit_many(
        self,
        token_ids: Sequence[int],
        user_address: str,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Deposit given tokens from root chain to child."""
        self.check_for_root()
        self._validate_many(token_ids)
        amount_in_abi = self.client.parent.encode_parameters([token_ids], ['uint256[]'])
        return self.root_chain_manager.deposit(
            user_address,
            self.address,
            amount_in_abi,
            private_key,
            option,
        )

    def withdraw_start(
        self,
        token_id: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Begin withdrawal to root chain (on child chain)."""
        self.check_for_child()
        method = self.method('withdraw', token_id)
        return self.process_write(method, option, private_key)

    def withdraw_start_with_metadata(
        self,
        token_id: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Begin withdrawal to root chain with writing of metadata (on child chain)."""
        self.check_for_child()
        method = self.method('withdrawWithMetadata', token_id)
        return self.process_write(method, option, private_key)

    def withdraw_start_many(
        self,
        token_ids: Sequence[int],
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Begin withdrawal of multiple tokens to root chain (on child chain)."""
        self.check_for_child()
        self._validate_many(token_ids)
        method = self.method('withdrawBatch', token_ids)
        return self.process_write(method, option, private_key)

    def withdraw_exit_on_index(
        self,
        burn_transaction_hash: bytes,
        index: int,
        private_key: str | None = None,
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

    def is_withdraw_exited_many(self, tx_hash: bytes) -> bool:
        """Check if batch withdrawal is already exited for given transaction."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_721_BATCH_TRANSFER)

    def is_withdraw_exited_on_index(self, tx_hash: bytes, index: int) -> bool:
        """Check if withdrawal is already exited for given transaction on index."""
        return self.is_withdrawn_on_index(
            tx_hash, index, LogEventSignature.ERC_721_TRANSFER
        )

    def transfer(
        self,
        token_id: int,
        from_: str,
        to: str,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer to another user."""
        return self.transfer_erc_721(from_, to, token_id, private_key, option)
