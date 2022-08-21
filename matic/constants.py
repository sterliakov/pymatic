from __future__ import annotations

from typing import Final, final

from eth_typing import HexAddress, HexStr

MAX_AMOUNT: Final = 2**256 - 1
"""Max transaction amount."""

MATIC_TOKEN_ADDRESS_ON_POLYGON: Final = HexAddress(
    HexStr('0x0000000000000000000000000000000000001010')
)
"""MATIC token address on polygon network."""


@final
class POSLogEventSignature:
    """Signatures of different transfer kinds for POS bridge."""

    ERC_20_TRANSFER: Final = bytes.fromhex(
        'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    )
    """Transfer of ERC-20 token."""
    ERC_721_TRANSFER: Final = bytes.fromhex(
        'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    )
    """Transfer of ERC-721 token."""
    ERC_1155_TRANSFER: Final = bytes.fromhex(
        'c3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
    )
    """Transfer of ERC-1155 token."""
    ERC_721_BATCH_TRANSFER: Final = bytes.fromhex(
        'f871896b17e9cb7a64941c62c188a4f5c621b86800e3d15452ece01ce56073df'
    )
    """Batch transfer of ERC-721 token."""
    ERC_1155_BATCH_TRANSFER: Final = bytes.fromhex(
        '4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
    )
    """Batch transfer of ERC-1155 token."""
    ERC_721_TRANSFER_WITH_METADATA: Final = bytes.fromhex(
        'f94915c6d1fd521cee85359239227480c7e8776d7caf1fc3bacad5c269b66a14'
    )
    """Transfer of ERC-721 token with metadata."""
    STATE_SYNCED_EVENT: Final = bytes.fromhex(
        '103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392'
    )
    """StateSynced event signature."""


@final
class PlasmaLogEventSignature:
    """Signatures of different withdrawal kinds for plasma bridge."""

    ERC_20_WITHDRAW_EVENT_SIG = bytes.fromhex(
        'ebff2602b3f468259e1e99f613fed6691f3a6526effe6ef3e768ba7ae7a36c4f'
    )
    """Withdrawal of ERC-20 token event signature."""
    ERC_721_WITHDRAW_EVENT_SIG = bytes.fromhex(
        '9b1bfa7fa9ee420a16e124f794c35ac9f90472acc99140eb2f6447c714cad8eb'
    )
    """Withdrawal of ERC-721 token event signature."""
