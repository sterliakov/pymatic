from __future__ import annotations

from typing import Iterable, cast

from eth_typing import HexAddress

from matic.constants import MATIC_TOKEN_ADDRESS_ON_POLYGON
from matic.json_types import (
    IPlasmaClientConfig,
    IPlasmaContracts,
    ITransactionOption,
    ITransactionWriteResult,
)
from matic.plasma.contracts import DepositManager, RegistryContract, WithdrawManager
from matic.plasma.erc_20 import ERC20
from matic.plasma.erc_721 import ERC721
from matic.utils.bridge_client import BridgeClient
from matic.utils.exit_util import ExitUtil
from matic.utils.root_chain import RootChain

__all__ = ['PlasmaClient', 'ERC20', 'ERC721']


class PlasmaClient(BridgeClient[IPlasmaClientConfig]):
    """Plasma bridge client.

    Used to manage instantiation of
    :class:`matic.plasma.erc_20.ERC20` and :class:`matic.plasma.erc_721.ERC721`
    and perform some common operations.
    """

    withdraw_manager: WithdrawManager
    """Withdraw manager instance."""
    deposit_manager: DepositManager
    """Deposit manager instance."""
    registry: RegistryContract
    """Registry contract instance."""

    def __init__(self, config: IPlasmaClientConfig):
        super().__init__(config)

        main_contracts = self.client.main_plasma_contracts
        self.client.config.update(
            {
                'root_chain': main_contracts['RootChainProxy'],
                'registry': main_contracts['Registry'],
                'deposit_manager': main_contracts['DepositManagerProxy'],
                'withdraw_manager': main_contracts['WithdrawManagerProxy'],
            }
        )

        self.registry = RegistryContract(
            self.client, config['registry']  # type: ignore
        )
        self.deposit_manager = DepositManager(
            self.client, config['deposit_manager']  # type: ignore
        )
        self.exit_util = ExitUtil(
            self.client, RootChain(self.client, config['root_chain'])  # type: ignore
        )
        self.withdraw_manager = WithdrawManager(
            self.client, config['withdraw_manager']  # type: ignore
        )

    def _get_contracts(self) -> IPlasmaContracts:
        return IPlasmaContracts(
            deposit_manager=self.deposit_manager,
            exit_util=self.exit_util,
            registry=self.registry,
            withdraw_manager=self.withdraw_manager,
        )

    def erc_20(
        self, token_address: HexAddress | None, is_parent: bool = False
    ) -> ERC20:
        """Instantiate :class:`~matic.plasma.erc_20.ERC20` for token address.

        Args:
            token_address: address where token contract is deployed.
            is_parent: Whether this belongs to parent or child chain.
        """
        if token_address is None and not is_parent:
            token_address = MATIC_TOKEN_ADDRESS_ON_POLYGON
        if not token_address:
            raise ValueError('Token address required on parent chain.')

        return ERC20(token_address, is_parent, self.client, self._get_contracts)

    def erc_721(self, token_address: HexAddress, is_parent: bool = False) -> ERC721:
        """Instantiate :class:`~matic.plasma.erc_721.ERC721` for token address.

        Args:
            token_address: address where token contract is deployed.
            is_parent: Whether this belongs to parent or child chain.
        """
        return ERC721(token_address, is_parent, self.client, self._get_contracts)

    def withdraw_exit(
        self,
        tokens: HexAddress | Iterable[HexAddress],
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Perform withdraw exit."""
        return self.withdraw_manager.withdraw_exit(tokens, private_key, option)

    def deposit_ether(
        self,
        amount: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Deposit given amount of ether to polygon chain."""
        return ERC20(
            cast(HexAddress, ''), True, self.client, self._get_contracts
        )._deposit_ether(amount, private_key, option)
