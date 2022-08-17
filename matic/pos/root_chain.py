from __future__ import annotations

from typing import Any

from matic.json_types import IContractInitParam
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient

# import { BaseToken, utils, Web3SideChainClient } from "../utils"
# import { TYPE_AMOUNT } from "../types"
# import { IPOSClientConfig, ITransactionOption } from "../interfaces"
# import { BaseBigNumber } from ".."


class RootChain(BaseToken):
    def __init__(self, client: Web3SideChainClient, address: bytes):
        super().__init__(
            IContractInitParam(
                address=address,
                name='RootChain',
                is_parent=True,
            ),
            client=client,
        )

    def method(self, method_name: str, *args: Any) -> Any:
        return self.contract.method(method_name, *args)

    @property
    def last_child_block(self):
        return self.method('getLastChildBlock').read()

    def find_root_block_from_child(self, child_block_number: int) -> int:
        checkpoint_interval = 10000

        # First checkpoint id = start * 10000
        start = 1
        # Last checkpoint id = end * 10000
        method = self.method('currentHeaderBlock')
        current_header_block = method.read()
        end = int(current_header_block) // checkpoint_interval

        # Binary search on all the checkpoints to find the checkpoint
        # that contains the child_block_number
        ans = None
        while start <= end:
            if start == end:
                ans = start
                break
            mid = (start + end) // 2
            _, header_start, header_end, _, _ = self.method(
                'headerBlocks', mid * checkpoint_interval
            ).read()

            if header_start <= child_block_number <= header_end:
                # If child_block_number is between the upper and lower bounds
                # of the header_block, we found our answer
                ans = mid
                break
            elif header_start > child_block_number:
                # // child_block_number was checkpointed before self header
                end = mid - 1
            elif header_end < child_block_number:
                # // child_block_number was checkpointed after self header
                start = mid + 1

        assert ans is not None
        return ans * checkpoint_interval
