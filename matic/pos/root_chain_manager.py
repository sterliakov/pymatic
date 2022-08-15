from __future__ import annotations

from typing import Any

from matic.json_types import IContractInitParam, ITransactionOption
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient

# import { BaseToken, Web3SideChainClient } from "../utils"
# import { IPOSClientConfig, ITransactionOption } from "../interfaces"


class RootChainManager(BaseToken):
    def __init__(self, client: Web3SideChainClient, address: bytes):
        super().__init__(
            IContractInitParam(
                address=address,
                name='RootChainManager',
                bridge_type='pos',
                is_parent=True,
            ),
            client=client,
        )

    def method(self, method_name: str, *args: Any) -> Any:
        return self.contract.method(method_name, *args)

    def deposit(
        self,
        user_address: bytes,
        token_address: bytes,
        deposit_data: bytes,
        private_key: str,
        option: ITransactionOption | None = None,
    ):
        method = self.method('depositFor', user_address, token_address, deposit_data)
        return self.process_write(method, option, private_key)

    def exit(self, exit_payload: bytes, private_key: str, option: ITransactionOption):
        method = self.method('exit', exit_payload)
        return self.process_write(method, option, private_key)

    def is_exit_processed(self, exit_hash: bytes) -> Any:
        method = self.method('processedExits', exit_hash)
        return self.process_read(method)
