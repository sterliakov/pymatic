from __future__ import annotations

from typing import Iterable, Sequence

from matic.constants import LogEventSignature
from matic.json_types import IExitTransactionOption, ITransactionOption
from matic.pos.pos_token import TokenWithApproveAll


class ERC1155(TokenWithApproveAll):
    """Arbitrary ERC-1155-compliant token."""

    CONTRACT_NAME: str = 'ChildERC1155'
    BURN_EVENT_SIGNATURE: bytes = LogEventSignature.ERC_1155_TRANSFER

    @property
    def mintable_predicate_address(self) -> str | None:
        """Address of mintable predicte for this token."""
        return getattr(
            self.client.config, 'erc_1155_mintable_predicate', ''
        ) or self.client.get_config('Main.POSContracts.MintableERC1155PredicateProxy')

    def get_balance(
        self, user_address: str, token_id: int, option: ITransactionOption | None = None
    ) -> int:
        """Get balance of a user for supplied token."""
        method = self.method('balanceOf', user_address, token_id)
        return self.process_read(method, option)

    def approve_all_for_mintable(
        self, private_key: str | None = None, option: ITransactionOption | None = None
    ):
        """Approve all tokens for mintable token."""
        self.check_for_root()
        address = self.mintable_predicate_address
        assert address
        return self._approve_all(address, private_key, option)

    def deposit(
        self,
        amount: int,
        token_id: int,
        user_address: str,
        data: bytes | None = None,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Deposit supplied amount of token for a user."""
        self.check_for_root()
        return self.deposit_many(
            amounts=[amount],
            token_ids=[token_id],
            user_address=user_address,
            data=data or b'',
            private_key=private_key,
            option=option,
        )

    def deposit_many(
        self,
        amounts: Iterable[int],
        token_ids: Iterable[int],
        user_address: str,
        data: bytes | None = None,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Deposit supplied amount of multiple token for user."""
        self.check_for_root()

        amount_in_abi = self.client.parent.encode_parameters(
            [
                token_ids,
                amounts,
                data or b'',
            ],
            ['uint256[]', 'uint256[]', 'bytes'],
        )

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
        amount: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Start withdraw process by burning the required amount for a token."""
        self.check_for_child()

        method = self.method('withdrawSingle', token_id, amount)
        return self.process_write(method, option, private_key)

    def withdraw_start_many(
        self,
        token_ids: Sequence[int],
        amounts: Sequence[int],
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Start the withdraw process by burning multiple tokens at a time."""
        self.check_for_child()

        method = self.method('withdrawBatch', token_ids, amounts)
        return self.process_write(method, option, private_key)

    def withdraw_exit_many(
        self,
        burn_transaction_hash: bytes,
        private_key: str | None = None,
        option: IExitTransactionOption | None = None,
    ):
        """Exit the multiple withdraw process.

        Exit the withdraw process for many burned transaction and get the
        burned amount on root chain.

        This function fetches blocks and builds a proof manually.
        """
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            private_key,
            False,
            option=option,
        )

    def withdraw_exit_faster_many(
        self,
        burn_transaction_hash: bytes,
        private_key: str | None = None,
        option: IExitTransactionOption | None = None,
    ):
        """Exit the multiple withdraw process.

        Exit the withdraw process for many burned transaction and get the
        burned amount on root chain.

        This function uses API to get proof faster.
        """
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            private_key,
            True,
            option=option,
        )

    def is_withdraw_exited_many(self, tx_hash: bytes) -> bool:
        """Check if batch exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_1155_BATCH_TRANSFER)

    def transfer(
        self,
        from_: str,
        to: str,
        amount: int,
        token_id: int,
        data: bytes | None = b'',
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer the required amount of a token to another user."""
        return self.transfer_erc_1155(
            from_, to, amount, token_id, data, private_key, option
        )
