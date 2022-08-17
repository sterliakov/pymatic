from __future__ import annotations

from typing import Sequence

from matic.constants import LogEventSignature
from matic.json_types import (
    ITransactionOption,
    POSERC1155DepositBatchParam,
    POSERC1155DepositParam,
    POSERC1155TransferParam,
)
from matic.pos.pos_token import POSToken


class ERC1155(POSToken):
    CONTRACT_NAME: str = 'ChildERC1155'

    @property
    def mintable_predicate_address(self) -> str | None:
        return getattr(
            self.client.config, 'erc_1155_mintable_predicate', ''
        ) or self.client.get_config('Main.POSContracts.MintableERC1155PredicateProxy')

    def get_balance(
        self, user_address: str, token_id: int, option: ITransactionOption | None = None
    ) -> int:
        """Get balance of a user for supplied token."""
        method = self.contract.method('balanceOf', user_address, token_id)
        return self.process_read(method, option)

    def is_approved_all(
        self, user_address: str, option: ITransactionOption | None = None
    ) -> bool:
        """Check if a user is approved for all tokens."""
        self.check_for_root()

        method = self.contract.method(
            'isApprovedForAll', user_address, self.predicate_address
        )
        return bool(self.process_read(method, option))

    def _approve_all(
        self,
        predicate_address: str,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()
        method = self.contract.method('setApprovalForAll', predicate_address, True)
        return self.process_write(method, option, private_key)

    def approve_all(self, private_key: str, option: ITransactionOption | None = None):
        """Approve all tokens."""
        self.check_for_root()
        return self._approve_all(self.predicate_address, private_key, option)

    def approve_all_for_mintable(
        self, private_key: str, option: ITransactionOption | None = None
    ):
        """Approve all tokens for mintable token."""
        self.check_for_root()
        address = self.mintable_predicate_address
        assert address
        return self._approve_all(address, private_key, option)

    def deposit(
        self,
        param: POSERC1155DepositParam,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Deposit supplied amount of token for a user."""
        self.check_for_root()
        return self.deposit_many(
            dict(
                amounts=[param['amount']],
                token_ids=[param['token_id']],
                user_address=param['user_address'],
                data=param.get('data', b''),
            ),
            private_key,
            option,
        )

    def deposit_many(
        self,
        param: POSERC1155DepositBatchParam,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Deposit supplied amount of multiple token for user."""
        self.check_for_root()

        amount_in_abi = self.client.parent.encode_parameters(
            [
                param['token_ids'],
                param['amounts'],
                param.get('data', b''),
            ],
            ['uint256[]', 'uint256[]', 'bytes'],
        )

        return self.root_chain_manager.deposit(
            param['user_address'],
            self.contract_param.address,
            amount_in_abi,
            private_key,
            option,
        )

    def withdraw_start(
        self,
        token_id: int,
        amount: int,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Start withdraw process by burning the required amount for a token."""
        self.check_for_child()

        method = self.contract.method('withdrawSingle', token_id, amount)
        return self.process_write(method, option, private_key)

    def withdraw_start_many(
        self,
        token_ids: Sequence[int],
        amounts: Sequence[int],
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Start the withdraw process by burning multiple tokens at a time."""
        self.check_for_child()

        method = self.contract.method('withdrawBatch', token_ids, amounts)
        return self.process_write(method, option, private_key)

    def withdraw_exit(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Exit the withdraw process and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_TRANSFER,
            private_key,
            False,
            option,
        )

    def withdraw_exit_faster(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Exit the withdraw process and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_TRANSFER,
            private_key,
            True,
            option,
        )

    def withdraw_exit_many(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Exit the multiple withdraw process.

        Exit the withdraw process for many burned transaction and get the
        burned amount on root chain.

        This function fetches blocks and builds a proof manually.
        """
        self.check_for_root()
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            private_key,
            False,
            option,
        )

    def withdraw_exit_faster_many(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Exit the multiple withdraw process.

        Exit the withdraw process for many burned transaction and get the
        burned amount on root chain.

        This function uses API to get proof faster.
        """
        self.check_for_root()
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            private_key,
            True,
            option,
        )

    def is_withdraw_exited(self, tx_hash: bytes) -> bool:
        """Check if exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_1155_TRANSFER)

    def is_withdraw_exited_many(self, tx_hash: bytes) -> bool:
        """Check if batch exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_1155_BATCH_TRANSFER)

    def transfer(
        self,
        param: POSERC1155TransferParam,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Transfer the required amount of a token to another user."""
        return self.transfer_erc_1155(param, private_key, option)
