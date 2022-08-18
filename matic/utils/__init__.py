from __future__ import annotations

from typing import Any, Iterable

import sha3  # pysha3

from matic.abstracts import BaseWeb3Client
from matic.web3_client import Web3Client as Web3ClientClass

__all__ = ['keccak256', 'resolve', 'UnstoppableDomains', 'Web3Client']


def keccak256(list_of_bytes: Iterable[bytes]) -> bytes:
    """Compute the sha3_256 flavor hash.

    Args:
        list_of_bytes: A list of bytes to be hashed.

    Returns:
        bytes: Hash value in :class:`bytes` (32 bytes).

    Raises:
        TypeError: If ``bytes`` or ``bytearray`` is used instead of sequence as input.
    """
    if isinstance(list_of_bytes, (bytes, bytearray)):  # type: ignore[unreachable]
        raise TypeError(
            f"Expected sequence of bytes or bytearray's, got: {type(list_of_bytes)}"
        )

    m = sha3.keccak_256()
    for item in list_of_bytes:
        m.update(item)

    return m.digest()


def resolve(obj: dict[str, Any], path: str | Iterable[str]):
    """Get value from nested dictionary by dotted path."""
    if isinstance(path, str):
        path = path.split('.')
    for key in path:
        obj = obj[key]
    return obj


UnstoppableDomains: dict[str, str] = {}

Web3Client: type[BaseWeb3Client] = Web3ClientClass
"""This can be assigned to use any other client class."""
