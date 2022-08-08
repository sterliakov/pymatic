from __future__ import annotations

from typing import Any, Final

from typing_extensions import TypedDict

from matic.services import get_ABI, get_address
from matic.utils import resolve

# import { service } from "../services";
# import { resolve, promiseResolve } from ".";

# type T_ABI_CACHE = {
#     [network_name: str, version: str]: {
#         address: any,
#         abi: {
#             [bridge_type: str]: {
#                 [contract_name: str]: any
#             }
#         }
#     }
# }


class _CacheItem(TypedDict):
    address: Any
    abi: dict[str, dict[str, Any]]


CACHE: dict[tuple[str, str], _CacheItem] = {}
DEFAULT_BRIDGE_TYPE: Final = 'plasma'


class ABIManager:
    def __init__(self, network_name: str, version: str) -> None:
        self.network_name, self.version = network_name, version

        addr = get_address(network_name, version)
        CACHE[(network_name, version)] = {
            'address': addr,
            'abi': {},
        }

    def get_config(self, path: str) -> Any:
        return resolve(
            CACHE[(self.network_name, self.version)]['address'],
            path,
        )

    def get_ABI(
        self, contract_name: str, bridge_type: str | None = None
    ) -> dict[str, Any]:
        bridge_type = bridge_type or DEFAULT_BRIDGE_TYPE
        abi = (
            CACHE[(self.network_name, self.version)]['abi']
            .get(bridge_type, {})
            .get(contract_name)
        )
        if abi is not None:
            return abi

        abi = get_ABI(self.network_name, self.version, bridge_type, contract_name)
        self.set_ABI(contract_name, bridge_type, abi)
        return abi

    def set_ABI(
        self, contract_name: str, bridge_type: str, abi: dict[str, Any]
    ) -> None:
        abi_store = CACHE[(self.network_name, self.version)]['abi']
        abi_store.setdefault(bridge_type, {})[contract_name] = abi
