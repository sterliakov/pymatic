from __future__ import annotations

from logging import getLogger
from typing import Final

import matic.utils
from matic.abstracts import BaseWeb3Client
from matic.json_types import IBaseClientConfig
from matic.utils.abi_manager import ABIManager

# _T_conf = TypeVar('_T_conf')

# import { IBaseClientConfig } from "../interfaces"
# import { BaseWeb3Client } from "../abstracts"


class Web3SideChainClient:
    parent: BaseWeb3Client
    child: BaseWeb3Client

    # config: _T_conf

    abi_manager: ABIManager

    logger: Final = getLogger(__package__)

    # resolution: {}

    def __init__(self, config: IBaseClientConfig):
        # config.parent.default_config = config.parent.default_config or {}
        # config.child.default_config = config.child.default_config or {}
        self.config = config

        web3_client_cls = matic.utils.Web3Client
        if not web3_client_cls:
            raise ValueError('web3_client_cls is not set')

        self.resolution = matic.utils.UnstoppableDomains or None

        self.parent = web3_client_cls(
            getattr(config.parent, 'provider', None), self.logger
        )
        self.child = web3_client_cls(
            getattr(config.child, 'provider', None), self.logger
        )

        # self.logger.enableLog(config.log)

        try:
            self.abi_manager = ABIManager(config.network, config.version)
            self.logger.info('init called', self.abi_manager)
        except Exception as e:
            raise ValueError(
                f'network {config.network} - {config.version} is not supported'
            ) from e

    def get_ABI(self, name: str, type_: str | None = None):
        return self.abi_manager.get_ABI(name, type_)

    def get_config(self, path: str):
        return self.abi_manager.get_config(path)

    @property
    def main_plasma_contracts(self):
        return self.get_config('Main.Contracts')

    @property
    def main_POS_contracts(self):
        return self.get_config('Main.POSContracts')

    def is_EIP_1559_supported(self, is_parent: bool) -> bool:
        if is_parent:
            return self.get_config('Main.SupportsEIP1559')
        else:
            return self.get_config('Matic.SupportsEIP1559')
