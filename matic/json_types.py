from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Sequence

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
    """Transaction recipient."""
    value: int
    """MATIC (ETH) amount to send."""
    gas_limit: int
    """Upper limit of gas allowed to be spent during transaction execution."""
    gas_price: int
    """Upper limit of gas price."""
    data: bytes
    """Data to send."""
    nonce: int
    """Transaction nonce (number of previously sent transactions)."""
    chain_id: int
    """Chain id (5 for Goerli)."""
    chain: str
    """Chain name."""
    hardfork: str
    """Hard fork (London, Byzantium, Istanbul, ...)."""
    max_fee_per_gas: int
    """ERP-1159 fee specification."""
    max_priority_fee_per_gas: int
    """ERP-1159 fee specification."""
    type: str
    """Transaction type, hex string (0x)."""


class ITransactionOption(ITransactionRequestConfig):
    """Transaction config: this can be passed as option to almost all methods."""

    return_transaction: NotRequired[bool]
    """Skip writing step and return prepared transaction."""


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
    """Signature in case you need to adjust default used."""


@dataclass
class ITransactionData:
    """Transaction parameters that can be obtained from blockchain."""

    transaction_hash: bytes
    """Hash of transaction."""
    nonce: int
    """Transaction nonce."""
    block_hash: bytes | None
    """Hash of a block where transaction was included."""
    block_number: int | None
    """Number of a block where transaction was included."""
    transaction_index: int | None
    """Index of a transaction in the block."""
    from_: str
    """Sender."""
    to: str | None
    """Recipient."""
    value: int
    """Transferred token amount."""
    gas_price: int
    """Actual gas price."""
    gas: int
    """Gas amount used."""
    input: bytes
    """Binary input data."""


class NeighbourClientConfig(TypedDict):
    """Configuration for parent/child of :class:`~matic.utils.web3_side_chain_client.Web3SideChainClient`."""  # noqa

    provider: Any
    """Web3 provider to use."""
    default_config: ConfigWithFrom
    """Any required configuration (must include "from" key)."""


class IBaseClientConfig(TypedDict):
    """Configuration for :class:`~matic.utils.web3_side_chain_client.Web3SideChainClient`."""  # noqa

    network: str
    """Network to connect to - 'testnet' or 'mainnet'."""
    version: str
    """Network version - 'mumbai' or 'v1'."""
    parent: NotRequired[NeighbourClientConfig]
    """Parent chain configuration."""
    child: NotRequired[NeighbourClientConfig]
    """Child chain configuration."""


class IPOSClientConfig(IBaseClientConfig):
    """Configuration for POS client."""

    root_chain_manager: NotRequired[str]
    """Root chain manager address."""
    root_chain: NotRequired[str]
    """Root chain address."""
    erc_1155_mintable_predicate: NotRequired[str]
    """Mintable predicate for ERC-1155 token address."""


@dataclass
class IBaseBlock:
    """Base block parameters."""

    size: int
    """Block size."""
    difficulty: int
    """Block difficulty - how hard it was to mine it."""
    total_difficulty: int
    """Accumulated sum of all block difficulties till this one (inclusive)."""
    number: int
    """Block number."""
    hash: bytes
    """Block hash."""
    parent_hash: bytes
    """Hash of parent block."""
    nonce: int
    """Block nonce."""
    gas_limit: int
    """TOtal block gas limit."""
    gas_used: int
    """Used amount of gas."""
    timestamp: int
    """Moment when the block got mined."""
    logs_bloom: bytes
    """Binary representtion of logs Bloom filter."""
    transactions_root: bytes
    """Transactions trie root."""
    state_root: bytes
    """State trie root."""
    receipts_root: bytes
    """Receipts trie root."""
    miner: bytes
    """Miner signature."""
    extra_data: bytes
    """Any extra binary data that was attached to the block."""
    uncles: Sequence[bytes]
    """Blocks that got mined at the same time as this one (similar to orphan blocks)."""
    sha3_uncles: bytes
    """Hashes of uncles."""
    base_fee_per_gas: int | None = None
    """Minimal fee per gas unit in block."""


@dataclass
class IBlock(IBaseBlock):
    """Block with raw transactions (bytes)."""

    transactions: Sequence[bytes] = field(default_factory=list)
    """Encoded (binary) transactions data."""


@dataclass
class IBlockWithTransaction(IBaseBlock):
    """Block with decoded transactions."""

    transactions: Sequence[ITransactionData] = field(default_factory=list)
    """Decoded (dict-formatted) transactions data."""


@dataclass
class IPOSContracts:
    """Return type of ``get_pos_contracts`` parameter of :class:`matic.pos.pos_token.POSToken`."""  # noqa

    root_chain_manager: RootChainManager
    """Root chain manager."""
    exit_util: ExitUtil
    """Helper class instance for building exit data."""


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
    """JSON-RPC request parameters dict.

    Follows `specification <https://www.jsonrpc.org/specification>`_.
    """

    method: RPCEndpoint | str
    """Method name to call."""
    params: list[Any]
    """List of arguments."""
    id: NotRequired[str | int]
    """Identifier to match request and response."""
    jsonrpc: NotRequired[Literal['2.0']]
    """Protocol version."""


class IJsonRpcResponse(TypedDict):
    """JSON-RPC response parameters dict.

    Follows `specification <https://www.jsonrpc.org/specification>`_.
    """

    jsonrpc: Literal['2.0']
    """Protocol version."""
    id: int
    """Identifier to match request and response."""
    result: NotRequired[Any]
    """Call result."""
    error: NotRequired[str]
    """JSON error format."""


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
    """Log address."""
    data: str
    """Hashed log data (0x hex string)."""
    topics: Sequence[bytes]
    """List of binary topics values."""
    log_index: int
    """Index of log in the sequence."""
    transaction_hash: bytes
    """Hash of transaction this log is attached to."""
    transaction_index: int
    """Index of transaction this log is attached to."""
    block_hash: bytes
    """Hash of the block that includes transaction this log is attached to."""
    block_number: int
    """Number of the block that includes transaction this log is attached to."""
    removed: bool
    """Whether this log was removed."""


class _RawLogData(TypedDict):
    data: bytes
    """Hashed log data."""
    topics: Sequence[bytes]
    """List of binary topics values."""


@dataclass
class IEventLog:
    """Event logs (can occur in transaction receipts)."""

    event: str
    """Event name."""
    address: bytes
    """Event address."""
    return_values: Any
    """Event return values."""
    log_index: int
    """Index of log in the sequence."""
    transaction_hash: bytes
    """Hash of transaction this log is attached to."""
    transaction_index: int
    """Index of transaction this log is attached to."""
    block_hash: bytes
    """Hash of the block that includes transaction this log is attached to."""
    block_number: int
    """Number of the block that includes transaction this log is attached to."""
    raw: _RawLogData | None = None
    """Raw event data."""


@dataclass
class ITransactionReceipt:
    """Transaction receipt format used internally."""

    transaction_hash: bytes
    """Hash of transaction this log is attached to."""
    transaction_index: int
    """Index of transaction this log is attached to."""
    block_hash: bytes
    """Hash of the block that includes transaction this log is attached to."""
    block_number: int
    """Number of the block that includes transaction this log is attached to."""
    from_: bytes
    """Sender address."""
    to: bytes
    """Recipient address."""
    contract_address: bytes
    """Address of the contract transaction interacts with."""
    cumulative_gas_used: int
    """Total cumulative amount of gas used."""
    gas_used: int
    """Total amount of gas used."""
    logs_bloom: bytes
    """Binary logs Bloom filter representation."""
    root: bytes
    """Transaction root."""
    type: str
    """Transaction type (hex string: 0x)."""
    status: bool | None = None
    """Transaction status: 0 on failure, 1 on success."""
    logs: Sequence[ILog] = field(default_factory=list)
    """Logs data."""
    events: dict[str, IEventLog] = field(default_factory=dict)
    """Events data."""


@dataclass
class CheckpointedBlock(IRootBlockInfo):
    """Block info obtained from API to construct a proof."""

    header_block_number: int
    """Header block number."""
    block_number: int
    """Number of a block."""
    start: int
    """Block start."""
    end: int
    """Block end."""
    proposer: str  # hex string, with "0x"
    """Block proposer address."""
    root: str  # hex string, with "0x"
    """Block root."""
    created_at: int
    """Block creation timestamp."""
    message: str
    """Message attached to the block."""
