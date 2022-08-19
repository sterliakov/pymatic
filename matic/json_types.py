from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Sequence

from typing_extensions import NotRequired, Required, TypedDict
from web3.types import RPCEndpoint

if TYPE_CHECKING:
    from matic.pos.exit_util import ExitUtil
    from matic.pos.root_chain_manager import RootChainManager


ConfigWithFrom = TypedDict('ConfigWithFrom', {'from': Required[str]})
"""Configuration dictionary with required key "from" (type str) and any other keys."""


class ITransactionRequestConfig(ConfigWithFrom, total=False):
    """Transaction config - an actual configuration used to interact with chain."""

    to: str
    value: int
    gas_limit: int
    gas_price: int
    data: bytes
    nonce: int
    chain_id: int
    chain: str
    hardfork: str
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    type: int


class ITransactionOption(ITransactionRequestConfig):
    """Transaction config: this can be passed as option to almost all methods."""

    return_transaction: NotRequired[bool]


class IAllowanceTransactionOption(ITransactionOption):
    """Transaction config for approve/allowance methods."""

    spender_address: NotRequired[bytes]
    """Address of spender.

    **spender** - third-party user or a smart contract which can transfer
    your token on your behalf.
    """


class IExitTransactionOption(ITransactionOption):
    """Transaction config for ``withdraw_exit_*`` operations."""

    burn_event_signature: NotRequired[bytes]


@dataclass
class ITransactionData:
    """Transaction parameters that can be obtained from blockchain."""

    transaction_hash: bytes
    nonce: int
    block_hash: bytes | None
    block_number: int | None
    transaction_index: int | None
    from_: str
    to: str | None
    value: int
    gas_price: int
    gas: int
    input: bytes


class NeighbourClientConfig(TypedDict):
    """Configuration for parent/child of :class:`~matic.utils.web3_side_chain_client.Web3SideChainClient`."""  # noqa

    provider: Any
    default_config: ConfigWithFrom


class IBaseClientConfig(TypedDict):
    """Configuration for :class:`~matic.utils.web3_side_chain_client.Web3SideChainClient`."""  # noqa

    network: str
    """Network to connect - 'testnet' or 'mainnet'."""
    version: str
    """Network version - 'mumbai' or 'v1'."""
    parent: NotRequired[NeighbourClientConfig]
    """Parent chain configuration."""
    child: NotRequired[NeighbourClientConfig]
    """Child chain configuration."""
    log: NotRequired[bool]


class IPOSClientConfig(IBaseClientConfig):
    """Configuration for POS client."""

    root_chain_manager: NotRequired[str]
    root_chain: NotRequired[str]
    erc_1155_mintable_predicate: NotRequired[str]


@dataclass
class IBaseBlock:
    """Base block parameters."""

    size: int
    difficulty: int
    total_difficulty: int
    uncles: Sequence[bytes]
    number: int
    hash: bytes
    parent_hash: bytes
    nonce: int
    sha3_uncles: bytes
    logs_bloom: bytes
    transactions_root: bytes
    state_root: bytes
    receipts_root: bytes
    miner: bytes
    extra_data: bytes
    gas_limit: int
    gas_used: int
    timestamp: int
    base_fee_per_gas: int | None = None


@dataclass
class IBlock(IBaseBlock):
    """Block with raw transactions (bytes)."""

    transactions: Sequence[bytes] = field(default_factory=list)


@dataclass
class IBlockWithTransaction(IBaseBlock):
    """Block with decoded transactions."""

    transactions: Sequence[ITransactionData] = field(default_factory=list)


@dataclass
class IPOSContracts:
    """Return type of ``get_pos_contracts`` parameter of :class:`matic.pos.POSToken`."""

    root_chain_manager: RootChainManager
    exit_util: ExitUtil


@dataclass
class IRootBlockInfo:
    """Root block info (used in proofs)."""

    start: int
    """Block start number."""
    end: int
    """Block end number."""
    header_block_number: int
    """Header block number - root block number in which child block exist."""


class IJsonRpcRequestPayload(TypedDict):
    """JSON-RPC request parameters dict."""

    method: RPCEndpoint | str
    params: list[Any]
    id: NotRequired[str | int]


class IJsonRpcResponse(TypedDict):
    """JSON-RPC response parameters dict."""

    jsonrpc: str
    id: int
    result: NotRequired[Any]
    error: NotRequired[str]


class ITransactionWriteResult(ABC):
    """Interface for result of ``process_write`` method."""

    @property
    @abstractmethod
    def transaction_hash(self) -> bytes:
        """Get hash of executed transaction."""
        ...

    @property
    def receipt(self) -> ITransactionReceipt:
        """Property for convenient access to receipt."""
        return self.get_receipt()

    @abstractmethod
    def get_receipt(self, timeout: int = ...) -> ITransactionReceipt:
        """Get receipt (wait max ``timeout`` seconds)."""
        ...


@dataclass
class ILog:
    """Log data."""

    address: str
    data: str
    topics: Sequence[bytes]
    log_index: int
    transaction_hash: bytes
    transaction_index: int
    block_hash: bytes
    block_number: int
    removed: bool


class _RawLogData(TypedDict):
    data: bytes
    topics: Sequence[bytes]


@dataclass
class IEventLog:
    """Event logs (can occur in transaction receipts)."""

    event: str
    address: bytes
    return_values: Any
    log_index: int
    transaction_index: int
    transaction_hash: bytes
    block_hash: bytes
    block_number: int
    raw: _RawLogData | None = None


@dataclass
class ITransactionReceipt:
    """Transaction receipt format used internally."""

    transaction_hash: bytes
    transaction_index: int
    block_hash: bytes
    block_number: int
    from_: bytes
    to: bytes
    contract_address: bytes
    cumulative_gas_used: int
    gas_used: int
    logs_bloom: bytes
    root: bytes
    type: str
    status: bool | None = None
    logs: Sequence[ILog] = field(default_factory=list)
    events: dict[str, IEventLog] = field(default_factory=dict)


@dataclass
class CheckpointedBlock(IRootBlockInfo):
    """Block info obtained from API to construct a proof."""

    header_block_number: int
    block_number: int
    start: int
    end: int
    proposer: str  # hex string, with "0x"
    root: str  # hex string, with "0x"
    created_at: int
    message: str
