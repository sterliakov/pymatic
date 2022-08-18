from __future__ import annotations

from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class RootChain(BaseToken):
    """Root chain implementation.

    This represents a connection between parent (root) and child chains.
    For example, Goerli testnet is a root chain for Mumbai testnet.
    """

    def __init__(self, client: Web3SideChainClient, address: str):
        super().__init__(
            address=address,
            name='RootChain',
            is_parent=True,
            client=client,
        )

    @property
    def last_child_block(self) -> int:
        """Get last block number on child chain."""
        return self.method('getLastChildBlock').read()

    def find_root_block_from_child(self, child_block_number: int) -> int:
        """Find root block corresponding to child block of given number."""
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
