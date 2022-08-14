from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Sequence

from typing_extensions import NotRequired, Required, TypedDict
from web3.types import RPCEndpoint

if TYPE_CHECKING:
    from matic.pos.exit_util import ExitUtil
    from matic.pos.root_chain_manager import RootChainManager


_TDictWithFrom = TypedDict('_TDictWithFrom', {'from': Required[bytes]})


class ITransactionRequestConfig(_TDictWithFrom, total=False):
    to: bytes
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
    return_transaction: NotRequired[bool]


class IAllowanceTransactionOption(ITransactionOption):
    spender_address: NotRequired[bytes]
    """Address of spender.

    **spender** - third-party user or a smart contract which can transfer
    your token on your behalf.
    """


@dataclass
class ITransactionData:
    transaction_hash: bytes
    nonce: int
    block_hash: bytes | None
    block_number: int | None
    transaction_index: int | None
    from_: bytes
    to: bytes | None
    value: int
    gas_price: int
    gas: int
    input: bytes


IApproveTransactionOption = IAllowanceTransactionOption  # FIXME: remove


@dataclass
class ConfigWithFrom:
    from_: bytes


@dataclass
class NeighbourClientConfig:
    provider: Any
    default_config: ConfigWithFrom


@dataclass
class IBaseClientConfig:
    network: str
    version: str
    parent: NeighbourClientConfig | None = None
    child: NeighbourClientConfig | None = None
    log: bool = True
    # request_concurrency: NotRequired[int]


@dataclass
class IBaseBlock:
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
    transactions: Sequence[bytes] = field(default_factory=list)


@dataclass
class IBlockWithTransaction(IBaseBlock):
    transactions: Sequence[ITransactionData] = field(default_factory=list)


@dataclass
class IContractInitParam:
    address: bytes
    is_parent: bool
    name: str
    """Used to get the predicate."""
    bridge_type: str | None = None  # was NotRequired


class IExitTransactionOption(ITransactionOption):
    burn_event_signature: NotRequired[bytes]


class IMethod(TypedDict, total=False):
    name: Required[str]
    call: Required[str]
    params: int
    input_formatter: Sequence[Callable[[], None] | None]
    output_formatter: Callable[[], None]
    transform_payload: Callable[[], None]
    extra_formatters: Any
    default_block: str
    default_account: str | None
    abi_coder: Any
    handle_revert: bool


class IPOSERC1155Address(TypedDict):
    mintable_predicate: NotRequired[str]


@dataclass
class IPOSClientConfig(IBaseClientConfig):
    root_chain_manager: bytes | None = None
    root_chain: bytes | None = None
    erc_1155: IPOSERC1155Address | None = None


@dataclass
class IPOSContracts:
    root_chain_manager: RootChainManager
    exit_util: ExitUtil


@dataclass
class IRootBlockInfo:
    start: str
    """Block start number."""
    end: str
    """Block end number."""
    header_block_number: int
    """Header block number - root block int in which child block exist."""


class IJsonRpcRequestPayload(TypedDict):
    method: RPCEndpoint
    params: list[Any]
    id: NotRequired[str | int]


class IJsonRpcResponse(TypedDict):
    jsonrpc: str
    id: int
    result: NotRequired[Any]
    error: NotRequired[str]


class ITransactionResult(ABC):
    @abstractmethod
    def estimate_gas(self, tx: ITransactionRequestConfig | None = None) -> int:
        ...

    @abstractmethod
    def encode_ABI(self) -> bytes:
        ...


class ITransactionWriteResult(ABC):
    @property
    @abstractmethod
    def transaction_hash(self) -> bytes:
        ...

    @property
    def receipt(self) -> ITransactionReceipt:
        return self.get_receipt()

    @abstractmethod
    def get_receipt(self, timeout: int = ...) -> ITransactionReceipt:
        ...


@dataclass
class ILog:
    address: bytes
    data: bytes
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


# FIXME: goes to pos/...
@dataclass
class POSERC1155DepositParam:
    token_id: int
    amount: int
    user_address: bytes
    data: bytes | None = None


@dataclass
class POSERC1155DepositBatchParam:
    token_ids: Sequence[int]
    amounts: Sequence[int]
    user_address: bytes
    data: bytes | None = None


@dataclass
class POSERC1155TransferParam:
    token_id: int
    amount: int
    from_: bytes
    to: bytes
    data: bytes | None = None
