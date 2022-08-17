from __future__ import annotations

from matic.constants import MAX_AMOUNT, LogEventSignature
from matic.exceptions import NullSpenderAddressException
from matic.json_types import (
    IAllowanceTransactionOption,
    IApproveTransactionOption,
    IExitTransactionOption,
    ITransactionOption,
)
from matic.pos.pos_token import POSToken

# import { ITransactionOption } from "../interfaces"
# import { Converter, Web3SideChainClient } from "../utils"
# import { POSToken } from "./pos_token"
# import { ERROR_TYPE, Log_Event_Signature } from "../enums"
# import { MAX_AMOUNT, promiseResolve } from ".."
# import { IAllowanceTransactionOption, IApproveTransactionOption, IExitTransactionOption, IPOSClientConfig, IPOSContracts } from "../interfaces"


class ERC20(POSToken):
    CONTRACT_NAME: str = 'ChildERC20'

    def get_balance(
        self, user_address: str, option: ITransactionOption | None = None
    ) -> int:
        """Get balance of a user for supplied token."""
        method = self.contract.method(
            'balanceOf',
            user_address,
        )
        return self.process_read(method, option)

    def get_allowance(
        self, user_address: str, option: IAllowanceTransactionOption | None = None
    ):
        """Get allowance of user."""
        predicate_address = (
            option['spender_address'] if option else None
        ) or self.predicate_address

        method = self.contract.method(
            'allowance',
            user_address,
            predicate_address,
        )
        return self.process_read(method, option)

    def approve(
        self,
        amount: int,
        private_key: str,
        option: IApproveTransactionOption | None = None,
    ):
        option = option or {}

        spender_address = option.get('spender_address')
        if not spender_address and not self.contract_param.is_parent:
            raise NullSpenderAddressException

        predicate_address = (
            spender_address if spender_address else self.predicate_address
        )

        method = self.contract.method('approve', predicate_address, amount)
        return self.process_write(method, option, private_key)

    def approve_max(
        self, private_key: str, option: IApproveTransactionOption | None = None
    ):
        return self.approve(MAX_AMOUNT, private_key, option)

    def deposit(
        self,
        amount: int,
        user_address: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Deposit given amount of token for user."""
        self.check_for_root()

        option = option or {}

        amount_in_ABI = self.client.parent.encode_parameters([amount], ['uint256'])
        return self.root_chain_manager.deposit(
            user_address,
            self.contract_param.address,
            amount_in_ABI,
            private_key,
            option,
        )

    def _deposit_ether(
        self,
        amount: int,
        user_address: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()

        option = option or {}

        method = self.root_chain_manager.method('depositEtherFor', user_address)
        return self.process_write(method, option, private_key)

    def withdraw_start(
        self,
        amount: int,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        """Initiate withdraw by burning provided amount."""
        self.check_for_child()

        option = option or {}

        method = self.contract.method('withdraw', amount)
        return self.process_write(method, option, private_key)

    def _withdraw_exit(
        self,
        burn_transaction_hash: bytes,
        is_fast: bool,
        private_key: str,
        option: IExitTransactionOption | None = None,
    ):
        event_signature = (
            option['burn_event_signature']
            if option and option.get('burn_event_signature')
            else LogEventSignature.ERC_20_TRANSFER
        )

        payload = self.exit_util.build_payload_for_exit(
            burn_transaction_hash, 0, event_signature, is_fast
        )
        return self.root_chain_manager.exit(payload, private_key, option or {})

    def withdraw_exit(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: IExitTransactionOption | None = None,
    ):
        """
        Complete withdraw process after checkpoint has been submitted for the block containing burn tx.
        """
        self.check_for_root()
        return self._withdraw_exit(burn_transaction_hash, False, private_key, option)

    def withdraw_exit_faster(
        self,
        burn_transaction_hash: bytes,
        private_key: str,
        option: IExitTransactionOption | None = None,
    ):
        """
        Complete withdraw process after checkpoint has been submitted for the block containing burn tx.
        """
        self.check_for_root()
        return self._withdraw_exit(burn_transaction_hash, True, private_key, option)

    def is_withdraw_exited(self, burn_tx_hash: bytes):
        """Check if exit has been completed for a transaction hash."""
        return self.is_withdrawn(burn_tx_hash, LogEventSignature.ERC_20_TRANSFER)

    def transfer(
        self,
        amount: int,
        to: bytes,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer amount to another user."""
        return self.transfer_ERC_20(to, amount, private_key, option)
