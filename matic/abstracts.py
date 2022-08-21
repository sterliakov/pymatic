from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Sequence

from eth_typing import HexAddress
from web3.types import BlockIdentifier, RPCEndpoint, RPCResponse

from matic.json_types import (
    IBlock,
    IBlockWithTransaction,
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
    ITransactionWriteResult,
)


class BaseWeb3Client(ABC):
    """Web3 client reference implementation."""

    def __init__(self, provider: Any):
        self.provider = provider

    @abstractmethod
    def get_contract(self, address: HexAddress, abi: Any) -> BaseContract:
        """Obtain a contract from deployment address and ABI dictionary."""

    @abstractmethod
    def read(
        self,
        config: ITransactionRequestConfig,
        return_transaction: bool = False,
    ) -> Any:
        """Perform a reading (non-modifying) operation."""

    @abstractmethod
    def write(
        self,
        config: ITransactionRequestConfig,
        private_key: str | None = None,
        return_transaction: bool = False,
    ) -> ITransactionWriteResult:
        """Perform a writing (modifying) operation."""

    @property
    @abstractmethod
    def gas_price(self) -> int:
        """Current gas price."""

    @abstractmethod
    def estimate_gas(self, config: ITransactionRequestConfig) -> int:
        """Estimate gas amount for transaction."""

    @property
    @abstractmethod
    def chain_id(self) -> int:
        """Current chain id."""

    @abstractmethod
    def get_transaction_count(self, address: HexAddress, block_number: Any) -> int:
        """Get amount of transactions in specified block for given address."""

    @abstractmethod
    def get_transaction(self, transaction_hash: bytes) -> ITransactionData:
        """Obtain transaction object by hash."""

    @abstractmethod
    def get_transaction_receipt(self, transaction_hash: bytes) -> ITransactionReceipt:
        """Get receipt for transaction."""

    @abstractmethod
    def get_block(
        self,
        block_hash_or_block_number: BlockIdentifier,
    ) -> IBlock:
        """Get block (with raw transaction data) by hash or number."""

    @abstractmethod
    def get_block_with_transaction(
        self,
        block_hash_or_block_number: BlockIdentifier,
    ) -> IBlockWithTransaction:
        """Get block (with decoded transaction data) by hash or number."""

    def get_root_hash(self, start_block: int, end_block: int) -> bytes:
        """Get root hash for two blocks."""
        return bytes.fromhex(
            self.send_rpc_request(
                method=RPCEndpoint('eth_getRootHash'),
                params=[int(start_block), int(end_block)],
            )['result']
        )

    @abstractmethod
    def send_rpc_request(
        self, method: RPCEndpoint, params: Iterable[Any]
    ) -> RPCResponse:
        """Perform arbitrary RPC request."""

    @abstractmethod
    def encode_parameters(self, params: Sequence[Any], types: Sequence[str]) -> bytes:
        """Encode ABI parameters according to schema."""

    @abstractmethod
    def decode_parameters(self, encoded: bytes, types: Sequence[Any]) -> Sequence[Any]:
        """Decode binary data to ABI parameters according to schema."""

    @abstractmethod
    def etherium_sha3(self, types: Iterable[str], values: Iterable[Any]) -> bytes:
        """Calculate solidity keccak hash of given values (encoded as types)."""


class BaseContractMethod(ABC):
    """Reference implementation of class defining smart contract method."""

    def __init__(self, address: HexAddress, method: Any) -> None:
        self.address = address
        self.method = method

    @abstractmethod
    def read(
        self,
        tx: ITransactionRequestConfig | None = None,
        return_transaction: bool = False,
    ) -> Any:
        """Perform a read operation.

        This does not sign a transaction and does not affect the chain.
        """

    @abstractmethod
    def write(
        self,
        tx: ITransactionRequestConfig,
        private_key: str | None = None,
        return_transaction: bool = False,
    ) -> ITransactionWriteResult:
        """Perform a write operation.

        Transaction is signed (with given PK), affects the chain.
        """

    @abstractmethod
    def estimate_gas(self, tx: ITransactionRequestConfig) -> int:
        """Estimate gas for given transaction.

        Warning:
            This method may fail if your transaction is invalid or cannot be executed.
        """

    @abstractmethod
    def encode_abi(self) -> bytes:
        """Encode args according to method ABI and prepend the selector."""


class BaseContract(ABC):
    """Reference implementation of class defining smart contract."""

    def __init__(self, address: HexAddress):
        self.address = address

    @abstractmethod
    def method(self, method_name: str, *args: Any) -> BaseContractMethod:
        """Obtain a method object by name and call arguments."""
