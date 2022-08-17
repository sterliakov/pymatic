from __future__ import annotations

from typing import Iterable

import rlp
from mpt import MerklePatriciaTrie as BaseTrie
from mpt.nibble_path import NibblePath
from mpt.node import Node

from matic.abstracts import BaseWeb3Client
from matic.json_types import IBlockWithTransaction, ITransactionReceipt
from matic.utils import keccak256
from matic.utils.merkle_tree import MerkleTree
from matic.utils.polyfill import removeprefix

# Implementation adapted from Tom French's `matic-proofs` library used under MIT License
# https://github.com/TomAFrench/matic-proofs
# FIXME: must be module, not class


class Trie(BaseTrie):
    def find_path(self, encoded_key):
        path = NibblePath(encoded_key)
        yield from self._find_path(self._root, path)

    def _find_path(self, node_ref, path):
        node = self._get_node(node_ref)

        # If path is empty, our travel is over.
        # Main `get` method will check if this node has a value.
        if len(path) == 0:
            yield node
            return

        if isinstance(node, Node.Leaf):
            # If we found a leaf, it's either the leaf we're looking for or wrong one.
            if node.path == path:
                yield node
                return
        elif isinstance(node, Node.Extension):
            # If we found an extension, we need to go deeper.
            if path.starts_with(node.path):
                for _ in range(len(node.path)):
                    yield node.path[path.at(0)]
                    path.consume(1)
                yield from self._find_path(node.next_ref, path)
                return
        elif isinstance(node, Node.Branch):
            # If we found a branch node, go to the appropriate branch.
            curr = path.at(0)
            yield node
            path.consume(1)
            branch = node.branches[curr]
            if len(branch) > 0:
                yield from self._find_path(branch, path)
                return

        raise KeyError


class ProofUtil:
    @classmethod
    def get_fast_merkle_proof(
        cls,
        web3: BaseWeb3Client,
        block_number: int,
        start_block: int,
        end_block: int,
    ):
        tree_depth = MerkleTree.estimate_depth(end_block - start_block + 1)

        # We generate the proof root down, whereas we need from leaf up
        reversed_proof: list[str] = []

        offset = start_block
        target_index = block_number - offset
        left_bound = 0
        right_bound = end_block - offset

        for depth in range(tree_depth):
            n_leaves = 2 ** (tree_depth - depth)

            # The pivot leaf is the last leaf which is included in the left subtree
            pivot_leaf = left_bound + n_leaves // 2 - 1

            if target_index > pivot_leaf:
                # Get the root hash to the merkle subtree to the left
                new_left_bound = pivot_leaf + 1
                # eslint-disable-next-line no-await-in-loop
                subtree_merkle_root = cls.query_root_hash(
                    web3, offset + left_bound, offset + pivot_leaf
                )
                reversed_proof.append(subtree_merkle_root)
                left_bound = new_left_bound
            else:
                # Things are more complex when querying to the right.
                # Root hash may come some layers down so we need to build a full tree
                # by padding with zeros.
                # Some trees may be completely empty.
                new_right_bound = min(right_bound, pivot_leaf)

                # Expect the tree to have a height one less than the current layer
                expected_height = tree_depth - (depth + 1)

                if right_bound <= pivot_leaf:
                    # Tree is empty so we repeatedly hash zero to correct height
                    subtree_merkle_root = cls.recursive_zero_hash(expected_height, web3)
                    reversed_proof.append(subtree_merkle_root)
                else:
                    # Height of tree given by RPC node
                    sub_tree_height = MerkleTree.estimate_depth(
                        right_bound - pivot_leaf
                    )

                    # Find the difference in height between this and the subtree we want
                    height_difference = expected_height - sub_tree_height

                    # For every extra layer we need to fill 2*n leaves filled with the
                    # merkle root of a zero-filled Merkle tree
                    # We need to build a tree which has height_difference layers

                    # The first leaf will hold the root hash as returned by the RPC
                    # eslint-disable-next-line no-await-in-loop
                    remaining_nodes_hash = cls.query_root_hash(
                        web3, offset + pivot_leaf + 1, offset + right_bound
                    )

                    # The remaining leaves will hold the merkle root of a zero-filled
                    # tree of height sub_tree_height
                    leaf_roots = cls.recursive_zero_hash(sub_tree_height, web3)

                    # Build a merkle tree of correct size for the subtree using
                    # these merkle roots
                    leaves = [bytes(leaf_roots) for _ in range(2**height_difference)]
                    leaves[0] = remaining_nodes_hash
                    subtree_merkle_root = MerkleTree(leaves).root
                    reversed_proof.append(subtree_merkle_root)

                right_bound = new_right_bound

        return reversed_proof[::-1]

    @classmethod
    def build_block_proof(
        cls,
        matic_web3: BaseWeb3Client,
        start_block: int,
        end_block: int,
        block_number: int,
    ):
        proof = cls.get_fast_merkle_proof(
            matic_web3, block_number, start_block, end_block
        )
        return b''.join(map(bytes.fromhex, proof)).hex()

    @classmethod
    def query_root_hash(cls, client: BaseWeb3Client, start_block: int, end_block: int):
        return client.get_root_hash(start_block, end_block)

    @classmethod
    def recursive_zero_hash(cls, n: int, client: BaseWeb3Client) -> bytes:
        if n == 0:
            return bytes(32)

        sub_hash = cls.recursive_zero_hash(n - 1, client)
        return keccak256([client.encode_parameters([sub_hash] * 2, ['bytes32'] * 2)])

    @classmethod
    def get_receipt_proof(
        cls,
        receipt: ITransactionReceipt,
        block: IBlockWithTransaction,
        web3: BaseWeb3Client,
        request_concurrency: int | None = None,
        receipts_val: Iterable[ITransactionReceipt] | None = None,
    ):
        state_sync_tx_hash = cls.get_state_sync_tx_hash(block).hex()
        receipts_trie = Trie({})

        receipts = receipts_val or [  # TODO: can be done in parallel
            web3.get_transaction_receipt(tx.transaction_hash)
            for tx in block.transactions
            if tx.transaction_hash != state_sync_tx_hash
        ]

        for sibling in receipts:
            path = rlp.encode(sibling.transaction_index)
            raw_receipt = cls.get_receipt_bytes(sibling)
            receipts_trie.update(path, raw_receipt)

        stack = list(receipts_trie.find_path(rlp.encode(receipt.transaction_index)))
        node = stack[-1]

        def node_to_raw(node: Node.Leaf | Node.Branch | Node.Extension) -> list[bytes]:
            if isinstance(node, Node.Leaf):
                return [node.path.encode(True), node.data]
            elif isinstance(node, Node.Extension):
                return [node.path.encode(False), node.data]
            elif isinstance(node, Node.Branch):
                return [*node.branches, node.data]
            else:
                raise ValueError('Unknown node type.')

        return {
            'block_hash': receipt.block_hash,
            'parent_nodes': list(map(node_to_raw, stack)),
            'root': block.receipts_root,
            'path': rlp.encode(receipt.transaction_index),
            'value': (
                node.data if cls.is_typed_receipt(receipt) else rlp.decode(node.data)
            ),
        }

    @classmethod
    def is_typed_receipt(cls, receipt: ITransactionReceipt) -> bool:
        return bool(receipt.status is not None and receipt.type not in {'0x0', '0x'})

    @classmethod
    def get_state_sync_tx_hash(cls, block) -> bytes:
        """
        get_state_sync_tx_hash returns block's tx hash for state-sync receipt
        Bor blockchain includes extra receipt/tx for state-sync logs,
        but it is not included in transactionRoot or receiptRoot.
        So, while calculating proof, we have to exclude them.

        This is derived from block's hash and int
        state-sync tx hash = keccak256("matic-bor-receipt-" + block.int + block.hash)
        """
        return keccak256(
            [
                # prefix for bor receipt
                b'matic-bor-receipt-',
                block.number.to_bytes(8, 'big'),  # 8 bytes of block number (BigEndian)
                block.hash,  # block hash
            ]
        )

    @classmethod
    def get_receipt_bytes(cls, receipt: ITransactionReceipt):
        encoded_data = rlp.encode(
            [
                (
                    (b'\x01' if receipt.status else b'')
                    if receipt.status is not None
                    else receipt.root
                ),
                receipt.cumulative_gas_used,
                receipt.logs_bloom,
                # encoded log array
                [
                    # [address, [topics array], data]
                    [
                        bytes.fromhex(removeprefix(log.address, '0x')),
                        log.topics,
                        bytes.fromhex(removeprefix(log.data, '0x')),
                    ]
                    for log in receipt.logs
                ],
            ]
        )
        if cls.is_typed_receipt(receipt):
            encoded_data = int(receipt.type, 0).to_bytes(1, 'big') + encoded_data

        return encoded_data

    # @classmethod
    # def get_raw_header(cls, block):
    #     raise NotImplementedError
