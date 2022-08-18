from __future__ import annotations

from typing import Any, Final

from typing_extensions import TypedDict

from matic.services import get_abi, get_address
from matic.utils import resolve


class _CacheItem(TypedDict):
    address: Any
    abi: dict[str, dict[str, Any]]


CACHE: dict[tuple[str, str], _CacheItem] = {}
DEFAULT_BRIDGE_TYPE: Final = 'plasma'


class ABIManager:
    """Caching manager for fetched contract ABI dicts."""

    def __init__(self, network_name: str, version: str) -> None:
        self.network_name, self.version = network_name, version

        addr = get_address(network_name, version)
        CACHE[(network_name, version)] = {
            'address': addr,
            'abi': {},
        }

    def get_config(self, path: str) -> Any:
        """Get option from cache item by dotted path."""
        return resolve(
            CACHE[(self.network_name, self.version)]['address'],
            path,
        )

    def get_abi(
        self, contract_name: str, bridge_type: str | None = None
    ) -> dict[str, Any]:
        """Get ABI dict for contract and memoise it."""
        bridge_type = bridge_type or DEFAULT_BRIDGE_TYPE
        abi = (
            CACHE[(self.network_name, self.version)]['abi']
            .get(bridge_type, {})
            .get(contract_name)
        )
        if abi is not None:
            return abi

        abi = get_abi(self.network_name, self.version, bridge_type, contract_name)
        self.set_abi(contract_name, bridge_type, abi)
        return abi

    def set_abi(
        self, contract_name: str, bridge_type: str, abi: dict[str, Any]
    ) -> None:
        """Store ABI dict in cache."""
        abi_store = CACHE[(self.network_name, self.version)]['abi']
        abi_store.setdefault(bridge_type, {})[contract_name] = abi
