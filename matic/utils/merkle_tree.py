from __future__ import annotations

from math import ceil, log2
from typing import Iterable, Sequence

from matic.utils import keccak256


class MerkleTree:
    leaves: list[bytes]
    layers: list[list[bytes]]

    def __init__(self, leaves: Sequence[bytes] | None = None):
        if not leaves:
            raise ValueError('At least 1 leaf needed')

        depth = self.estimate_depth(len(leaves))
        if depth > 20:
            raise ValueError('Depth must be 20 or less')

        self.leaves = [
            *leaves,
            *[bytes(32) for _ in range(2**depth - len(leaves))],
        ]

        self.layers = [self.leaves]
        self.create_hashes(self.leaves)

    @staticmethod
    def estimate_depth(size: int) -> int:
        return ceil(log2(size))

    @property
    def depth(self) -> int:
        return self.estimate_depth(len(self.leaves))

    def create_hashes(self, nodes: Sequence[bytes]) -> None:
        if len(nodes) == 1:
            return

        tree_level = [
            keccak256([left, right]) for left, right in zip(nodes[::2], nodes[1::2])
        ]

        # is odd number of nodes
        if len(nodes) % 2:
            tree_level.append(nodes[-1])

        self.layers.append(tree_level)
        self.create_hashes(tree_level)

    @property
    def root(self) -> bytes:
        return self.layers[-1][0]

    def get_proof(self, leaf: bytes) -> list[bytes]:
        index = next(i for i, item in enumerate(self.leaves) if item == leaf)

        if index is None:
            return []

        proof = []
        for layer in self.layers[:-1]:
            sibling_index = index + (-1 if index % 2 else 1)
            index //= 2
            proof.append(layer[sibling_index])

        return proof

    def verify(self, value, index, root, proof) -> bool:
        if not isinstance(proof, Iterable) or not value or not root:
            return False

        hash_ = value
        for node in proof:
            if index % 2:
                hash_ = keccak256([node, hash_])
            else:
                hash_ = keccak256([hash_, node])

            index //= 2

        return hash_ == root
