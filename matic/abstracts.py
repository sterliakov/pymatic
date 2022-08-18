from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger
from typing import Any, Iterable, Sequence

from matic.json_types import (
    IBlock,
    IBlockWithTransaction,
    IJsonRpcRequestPayload,
    IJsonRpcResponse,
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
    ITransactionWriteResult,
)


class BaseWeb3Client(ABC):
    def __init__(self, provider: Any, logger: Logger):
        self.provider = provider
        self.logger = logger

    @abstractmethod
    def get_contract(self, address: str, abi: Any) -> BaseContract:
        ...

    @abstractmethod
    def read(self, config: ITransactionRequestConfig) -> str:
        ...

    @abstractmethod
    def write(self, config: ITransactionRequestConfig) -> ITransactionWriteResult:
        ...

    @property
    @abstractmethod
    def gas_price(self) -> int:
        ...

    @abstractmethod
    def estimate_gas(self, config: ITransactionRequestConfig) -> int:
        ...

    @property
    @abstractmethod
    def chain_id(self) -> int:
        ...

    @abstractmethod
    def get_transaction_count(self, address: str, block_number: Any) -> int:
        ...

    @abstractmethod
    def get_transaction(self, transaction_hash: bytes) -> ITransactionData:
        ...

    @abstractmethod
    def get_transaction_receipt(self, transaction_hash: bytes) -> ITransactionReceipt:
        ...

    # @abstractmethod
    # def extend(property: str, methods: IMethod[])

    @abstractmethod
    def get_block(self, block_hash_or_block_number) -> IBlock:
        ...

    @abstractmethod
    def get_block_with_transaction(
        self, block_hash_or_block_number
    ) -> IBlockWithTransaction:
        ...

    def get_root_hash(self, start_block: int, end_block: int) -> bytes:
        return bytes.fromhex(
            self.send_rpc_request(
                {
                    'method': 'eth_getRootHash',
                    'params': [int(start_block), int(end_block)],
                    'id': round(datetime.now().timestamp()),
                }
            )['result']
        )

    @abstractmethod
    def send_rpc_request(self, request: IJsonRpcRequestPayload) -> IJsonRpcResponse:
        ...

    @abstractmethod
    def encode_parameters(self, params: Sequence[Any], types: Sequence[Any]) -> bytes:
        ...

    @abstractmethod
    def decode_parameters(self, encoded: bytes, types: Sequence[Any]) -> Sequence[Any]:
        ...

    @abstractmethod
    def etherium_sha3(self, types: Iterable[str], values: Iterable[Any]) -> bytes:
        ...


class BaseContractMethod(ABC):
    def __init__(self, address: str, logger: Logger, method: Any) -> None:
        self.address = address
        self.logger = logger
        self.method = method

    @abstractmethod
    def read(self, tx: ITransactionRequestConfig | None = None) -> Any:
        ...

    @abstractmethod
    def write(
        self, tx: ITransactionRequestConfig, private_key: str | None = None
    ) -> ITransactionWriteResult:
        ...

    @abstractmethod
    def estimate_gas(self, tx: ITransactionRequestConfig) -> int:
        ...

    @abstractmethod
    def encode_abi(self) -> Any:
        ...


class BaseContract(ABC):
    def __init__(self, address: str, logger: Logger):
        self.address = address
        self.logger = logger

    @abstractmethod
    def method(self, method_name: str, *args: Any) -> BaseContractMethod:
        ...
