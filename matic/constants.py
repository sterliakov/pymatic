from __future__ import annotations

from typing import Final, final

MAX_AMOUNT: Final = 2**256 - 1
"""Max transaction amount."""


@final
class LogEventSignature:
    """Signatures of different transfer kinds."""

    ERC_20_TRANSFER: Final = bytes.fromhex(
        'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    )
    ERC_721_TRANSFER: Final = bytes.fromhex(
        'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    )
    ERC_1155_TRANSFER: Final = bytes.fromhex(
        'c3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
    )
    ERC_721_BATCH_TRANSFER: Final = bytes.fromhex(
        'f871896b17e9cb7a64941c62c188a4f5c621b86800e3d15452ece01ce56073df'
    )
    ERC_1155_BATCH_TRANSFER: Final = bytes.fromhex(
        '4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
    )
    ERC_721_TRANSFER_WITH_METADATA: Final = bytes.fromhex(
        'f94915c6d1fd521cee85359239227480c7e8776d7caf1fc3bacad5c269b66a14'
    )
    STATE_SYNCED_EVENT: Final = bytes.fromhex(
        '103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392'
    )
