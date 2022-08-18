from __future__ import annotations

from logging import getLogger
from typing import Any, Final

import matic.utils
from matic.abstracts import BaseWeb3Client
from matic.json_types import IBaseClientConfig
from matic.utils.abi_manager import ABIManager


class Web3SideChainClient:
    """Web3 client class for a side chain."""

    parent: BaseWeb3Client
    child: BaseWeb3Client
    abi_manager: ABIManager

    logger: Final = getLogger(__package__)

    def __init__(self, config: IBaseClientConfig) -> None:
        # config.parent.default_config = config.parent.default_config or {}
        # config.child.default_config = config.child.default_config or {}
        self.config = config

        web3_client_cls = matic.utils.Web3Client
        if not web3_client_cls:
            raise ValueError('web3_client_cls is not set')

        self.resolution = matic.utils.UnstoppableDomains or None

        self.parent = web3_client_cls(
            (config.get('parent') or {}).get('provider'), self.logger  # type: ignore
        )
        self.child = web3_client_cls(
            (config.get('child') or {}).get('provider'), self.logger  # type: ignore
        )

        try:
            self.abi_manager = ABIManager(config['network'], config['version'])
        except Exception as e:
            raise ValueError(
                f'network {config["network"]} - {config["version"]} is not supported'
            ) from e

    def get_abi(self, name: str, type_: str | None = None) -> dict[str, Any]:
        """Get ABI dictionary for given name and type."""
        return self.abi_manager.get_abi(name, type_)

    def get_config(self, path: str) -> Any:
        """Fetch configuration option by a dotted path."""
        return self.abi_manager.get_config(path)

    @property
    def main_plasma_contracts(self):
        """Parameters of plasma contracts."""
        return self.get_config('Main.Contracts')

    @property
    def main_pos_contracts(self):
        """Parameters of POS contracts."""
        return self.get_config('Main.POSContracts')

    def is_eip_1559_supported(self, is_parent: bool) -> bool:
        """Check if EIP-1559 (improved fee specification) is available for chain."""
        if is_parent:
            return self.get_config('Main.SupportsEIP1559')
        else:
            return self.get_config('Matic.SupportsEIP1559')
