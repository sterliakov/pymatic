from __future__ import annotations

from matic.json_types import IPOSClientConfig, IPOSContracts, ITransactionOption
from matic.pos.erc_20 import ERC20
from matic.pos.erc_721 import ERC721
from matic.pos.erc_1155 import ERC1155
from matic.pos.exit_util import ExitUtil
from matic.pos.root_chain import RootChain
from matic.pos.root_chain_manager import RootChainManager
from matic.utils.bridge_client import BridgeClient


class POSClient(BridgeClient):
    root_chain_manager: RootChainManager
    config: IPOSClientConfig

    def __init__(self, config: IPOSClientConfig):
        super().__init__(config)
        main_pos_contracts = self.client.main_pos_contracts
        config.root_chain_manager = (
            config.root_chain_manager or main_pos_contracts['RootChainManagerProxy']
        )
        config.root_chain = (
            config.root_chain or self.client.main_plasma_contracts['RootChainProxy']
        )
        self.client.config = config

        self.root_chain_manager = RootChainManager(
            self.client, config.root_chain_manager
        )

        self.exit_util = ExitUtil(
            self.client, RootChain(self.client, config.root_chain)
        )

    def erc_20(self, token_address, is_parent: bool = False):
        return ERC20(token_address, is_parent, self.client, self._get_contracts)

    def erc_721(self, token_address, is_parent: bool = False):
        return ERC721(token_address, is_parent, self.client, self._get_contracts)

    def erc_1155(self, token_address, is_parent: bool = False):
        return ERC1155(token_address, is_parent, self.client, self._get_contracts)

    def deposit_ether(
        self,
        amount: int,
        user_address: str,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        return ERC20(
            b'',
            True,
            self.client,
            self._get_contracts,
        )._deposit_ether(amount, user_address, private_key, option)

    def _get_contracts(self) -> IPOSContracts:
        return IPOSContracts(
            exit_util=self.exit_util,
            root_chain_manager=self.root_chain_manager,
        )
