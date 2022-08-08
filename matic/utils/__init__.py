from __future__ import annotations

from typing import Any, Iterable

import sha3  # pysha3

from matic.abstracts import BaseWeb3Client

__all__ = ['keccak256', 'resolve', 'to_hex']


def keccak256(list_of_bytes: Iterable[bytes]) -> bytes:
    """Compute the sha3_256 flavor hash.

    Parameters
    ----------
    list_of_bytes : Iterable of bytes
        A list of bytes to be hashed.

    Returns
    -------
    Tuple[bytes, int]
        Hash value in :class:`bytes` (32 bytes) and length of bytes.

    Raises
    ------
    TypeError
        If ``bytes`` or ``bytearray`` is used instead of sequence as input.
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
    if isinstance(path, str):
        path = path.split('.')
    for key in path:
        obj = obj[key]
    return obj


def to_hex(amount: str | int):
    if isinstance(amount, int):
        return hex(amount)
    elif isinstance(amount, str):
        if amount.startswith('0x'):
            return amount
        return hex(int(amount, 0))
    raise ValueError(f'Expected str or int, got {amount.__class__}')


UnstoppableDomains: dict[str, str] = {}

Web3Client: type[BaseWeb3Client] = None
