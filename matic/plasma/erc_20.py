from __future__ import annotations

from typing import Callable

from eth_typing import HexAddress

from matic.abstracts import BaseContract
from matic.constants import (
    MATIC_TOKEN_ADDRESS_ON_POLYGON,
    MAX_AMOUNT,
    PlasmaLogEventSignature,
)
from matic.exceptions import NullSpenderAddressException
from matic.json_types import (
    IAllowanceTransactionOption,
    IPlasmaClientConfig,
    IPlasmaContracts,
    ITransactionOption,
    ITransactionWriteResult,
)
from matic.plasma.plasma_token import PlasmaToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class ERC20(PlasmaToken):
    """ERC-20-compliant token on plasma bridge."""

    WITHDRAW_EXIT_SIGNATURE = PlasmaLogEventSignature.ERC_20_WITHDRAW_EVENT_SIG
    """Withdraw event signature, used for exit methods."""

    def __init__(
        self,
        token_address: HexAddress,
        is_parent: bool,
        client: Web3SideChainClient[IPlasmaClientConfig],
        contracts: Callable[[], IPlasmaContracts],
    ):
        is_matic_token = token_address == MATIC_TOKEN_ADDRESS_ON_POLYGON
        super().__init__(
            is_parent=is_parent,
            address=token_address,
            name='MRC20' if is_matic_token else 'ChildERC20',
            client=client,
            get_helper_contracts=contracts,
        )

    @property
    def predicate(self) -> BaseContract:
        """Get predicate contract for token."""
        return self._fetch_predicate(
            'erc20Predicate',
            'ERC20Predicate',
            self.client.config.get('erc_20_predicate'),
        )

    def get_balance(
        self, user_address: HexAddress, option: ITransactionOption | None = None
    ) -> int:
        """Get user balance."""
        method = self.contract.method('balanceOf', user_address)
        return self.process_read(method, option)

    def get_allowance(
        self,
        user_address: HexAddress,
        option: IAllowanceTransactionOption | None = None,
    ) -> int:
        """Get allowance for the user."""
        option_fixed = self._check_option(option)
        spender_address = option_fixed.get('spender_address')
        method = self.contract.method(
            'allowance',
            user_address,
            spender_address or self.get_helper_contracts().deposit_manager.address,
        )
        return self.process_read(method, option_fixed)

    def approve(
        self,
        amount: int,
        private_key: str | None = None,
        option: IAllowanceTransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Approve spender to spend some tokens."""
        spender_address = option.get('spender_address') if option else None
        if not spender_address and not self.is_parent:
            raise NullSpenderAddressException

        method = self.contract.method(
            'approve',
            spender_address or self.get_helper_contracts().deposit_manager.address,
            amount,
        )
        return self.process_write(method, option, private_key)

    def approve_max(
        self,
        private_key: str | None = None,
        option: IAllowanceTransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Approve spender to spend all tokens."""
        return self.approve(MAX_AMOUNT, private_key, option)

    def deposit(
        self,
        amount: int,
        user_address: HexAddress,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Deposit amount of token for user."""
        self.check_for_root()

        contract = self.get_helper_contracts().deposit_manager.contract
        method = contract.method(
            'depositERC20ForUser',
            self.address,
            user_address,
            amount,
        )
        return self.process_write(method, option, private_key)

    def _deposit_ether(
        self,
        amount: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        self.check_for_root()

        option = self._check_option(option)
        contract = self.get_helper_contracts().deposit_manager.contract
        option['value'] = amount
        method = contract.method('depositEther')
        return self.process_write(method, option, private_key)

    def withdraw_start(
        self,
        amount: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Initialize withdrawal process."""
        self.check_for_child()

        if self.address == MATIC_TOKEN_ADDRESS_ON_POLYGON:
            option = self._check_option(option)
            option['value'] = amount

        method = self.contract.method('withdraw', amount)
        return self.process_write(method, option, private_key)

    def transfer(
        self,
        amount: int,
        to: HexAddress,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Transfer given amount of token to another user."""
        if self.address == MATIC_TOKEN_ADDRESS_ON_POLYGON:
            option = self._check_option(option)
            option['to'] = to
            option['value'] = amount
            return self.send_transaction(option, private_key)

        return self.transfer_erc_20(to, amount, private_key, option)
