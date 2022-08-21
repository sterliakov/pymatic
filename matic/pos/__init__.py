from __future__ import annotations

from typing import cast

from eth_typing import HexAddress

from matic.json_types import IPOSClientConfig, IPOSContracts, ITransactionOption
from matic.pos.erc_20 import ERC20
from matic.pos.erc_721 import ERC721
from matic.pos.erc_1155 import ERC1155
from matic.pos.root_chain_manager import RootChainManager
from matic.utils.bridge_client import BridgeClient
from matic.utils.exit_util import ExitUtil
from matic.utils.root_chain import RootChain

__all__ = ['POSClient', 'ERC20', 'ERC721', 'ERC1155']


class POSClient(BridgeClient[IPOSClientConfig]):
    """POS bridge client.

    Used to manage instantiation of
    :class:`matic.pos.erc_20.ERC20`,
    :class:`matic.pos.erc_721.ERC721` and
    :class:`matic.pos.erc_1155.ERC1155` classes
    and perform some common operations.
    """

    root_chain_manager: RootChainManager
    """Root chain manager."""

    def __init__(self, config: IPOSClientConfig):
        super().__init__(config)

        main_pos_contracts = self.client.main_pos_contracts
        config['root_chain_manager'] = (
            config.get('root_chain_manager')
            or main_pos_contracts['RootChainManagerProxy']
        )
        config['root_chain'] = (
            config.get('root_chain')
            or self.client.main_plasma_contracts['RootChainProxy']
        )
        self.client.config = config

        self.root_chain_manager = RootChainManager(
            self.client, config['root_chain_manager']
        )

        self.exit_util = ExitUtil(
            self.client, RootChain(self.client, config['root_chain'])
        )

    def erc_20(self, token_address: HexAddress, is_parent: bool = False) -> ERC20:
        """Instantiate :class:`~matic.pos.erc_20.ERC20` for token address.

        Args:
            token_address: address where token contract is deployed.
            is_parent: Whether this belongs to parent or child chain.
        """
        return ERC20(token_address, is_parent, self.client, self._get_contracts)

    def erc_721(self, token_address: HexAddress, is_parent: bool = False) -> ERC721:
        """Instantiate :class:`~matic.pos.erc_721.ERC721` for token address.

        Args:
            token_address: address where token contract is deployed.
            is_parent: Whether this belongs to parent or child chain.
        """
        return ERC721(token_address, is_parent, self.client, self._get_contracts)

    def erc_1155(self, token_address: HexAddress, is_parent: bool = False) -> ERC1155:
        """Instantiate :class:`~matic.pos.erc_1155.ERC1155` for token address.

        Args:
            token_address: address where token contract is deployed.
            is_parent: Whether this belongs to parent or child chain.
        """
        return ERC1155(token_address, is_parent, self.client, self._get_contracts)

    def deposit_ether(
        self,
        amount: int,
        user_address: HexAddress,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Deposit given amount of ether to polygon chain."""
        return ERC20(
            cast(HexAddress, ''),  # It won't be used
            True,
            self.client,
            self._get_contracts,
        )._deposit_ether(amount, user_address, private_key, option)

    def _get_contracts(self) -> IPOSContracts:
        return IPOSContracts(
            exit_util=self.exit_util,
            root_chain_manager=self.root_chain_manager,
        )
