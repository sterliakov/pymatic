from __future__ import annotations

from logging import Logger
from typing import Any, Iterable, Literal, Sequence, cast

from eth_abi import decode_abi, encode_abi
from hexbytes.main import HexBytes
from web3 import Web3
from web3.contract import Contract
from web3.method import Method
from web3.providers.base import BaseProvider
from web3.types import RPCEndpoint

from matic.abstracts import BaseContract, BaseContractMethod, BaseWeb3Client
from matic.json_types import (
    IBlock,
    IBlockWithTransaction,
    IJsonRpcRequestPayload,
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
    ITransactionWriteResult,
)
from matic.utils.polyfill import removeprefix
from matic.web3_client.utils import (
    matic_tx_request_config_to_web3,
    web3_receipt_to_matic_receipt,
    web3_tx_to_matic_tx,
)

__all__ = ['TransactionWriteResult', 'EthMethod', 'Web3Contract', 'Web3Client']


class TransactionWriteResult(ITransactionWriteResult):
    """Result of any writing call."""

    def __init__(self, tx_hash: bytes, client):
        self.tx_hash = tx_hash
        self.client = client

    def get_receipt(self, timeout: int = 120):
        """Get transaction receipt.

        Args:
            timeout: max seconds to wait.
        """
        receipt = self.client._web3.eth.wait_for_transaction_receipt(
            self.tx_hash, timeout=timeout
        )
        return web3_receipt_to_matic_receipt(receipt)

    @property
    def transaction_hash(self) -> bytes:
        """Hash of performed transaction."""
        return self.tx_hash


class EthMethod(BaseContractMethod):
    """Wrapper around web3 contract method (:class:`web3.method.Method`)."""

    def __init__(
        self, address: str, logger: Logger, method: Method[Any], client: Web3Client
    ) -> None:
        super().__init__(address, logger, method)
        self.method = method
        self.address = address
        self.client = client

    def read(self, tx: ITransactionRequestConfig | None = None):
        """Perform a read operation.

        This does not sign a transaction and does not affect the chain.
        """
        self.logger.debug('sending tx with config %s', tx)
        return self.method.call(matic_tx_request_config_to_web3(tx))

    def write(
        self,
        tx: ITransactionRequestConfig,
        private_key: str | None = None,
    ) -> TransactionWriteResult:
        """Perform a write operation.

        Transaction is signed (with given PK), affects the chain.
        """
        web3_tx = matic_tx_request_config_to_web3(tx)

        if private_key:
            tx_prep = self.method.build_transaction(web3_tx)
            self.logger.debug('Prepared tx: ', tx_prep)
            tx_signed = self.client._web3.eth.account.sign_transaction(
                tx_prep, private_key
            )
            res = self.client._web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        else:
            res = self.client._web3.eth.send_transaction(web3_tx)

        return TransactionWriteResult(res, self.client)

    def estimate_gas(self, tx: ITransactionRequestConfig) -> int:
        """Estimate gas for given transaction.

        Warning:
            This method may fail if your transaction is invalid or cannot be executed.
        """
        return self.method.estimate_gas(matic_tx_request_config_to_web3(tx))

    def encode_abi(self) -> bytes:
        """Encode args according to method ABI and prepend the selector."""
        abi = [e['type'] for e in self.method.abi['inputs']]
        return bytes.fromhex(removeprefix(self.method.selector, '0x')) + encode_abi(
            abi, self.method.args
        )


class Web3Contract(BaseContract):
    """A wrapper around web3 contract (:class:`web3.contract.Contract`)."""

    def __init__(
        self, address: str, contract: Contract, logger: Logger, client: Web3Client
    ):
        super().__init__(address, logger)
        self.contract = contract
        self.client = client

    def method(self, method_name: str, *args: Any) -> EthMethod:
        """Obtain a method object by name and call arguments."""
        self.logger.debug('method_name %s; args method %s', method_name, args)
        return EthMethod(
            self.address,
            self.logger,
            self.contract.get_function_by_name(method_name)(*args),
            self.client,
        )


class Web3Client(BaseWeb3Client):
    """Implementation of web3 client."""

    _web3: Web3

    def __init__(self, provider: BaseProvider, logger: Logger):
        from web3.middleware import geth_poa_middleware

        super().__init__(provider, logger)
        self._web3 = Web3(provider)
        self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def read(self, config: ITransactionRequestConfig):
        """Perform a reading (non-modifying) operation."""
        return self._web3.eth.call(matic_tx_request_config_to_web3(config))

    def write(self, config: ITransactionRequestConfig):
        """Perform a writing (modifying) operation."""
        return TransactionWriteResult(
            self._web3.eth.send_transaction(matic_tx_request_config_to_web3(config)),
            self,
        )

    def get_contract(self, address: str, abi: dict[str, Any]) -> Web3Contract:
        """Obtain a contract from deployment address and ABI dictionary."""
        cont = self._web3.eth.contract(abi=abi, address=cast(Any, address))
        return Web3Contract(address, cont, self.logger, self)

    @property
    def gas_price(self) -> int:
        """Current gas price."""
        return self._web3.eth.gas_price

    def estimate_gas(self, transaction: ITransactionRequestConfig) -> int:
        """Estimate gas amount for transaction."""
        return self._web3.eth.estimate_gas(matic_tx_request_config_to_web3(transaction))

    def get_transaction_count(self, address: str, block_number: int) -> int:
        """Get amount of transactions in specified block for given address."""
        return self._web3.eth.get_transaction_count(address, block_number)

    @property
    def chain_id(self):
        """Current chain id."""
        return self._web3.eth.chain_id

    def _ensure_transaction_not_null(self, data) -> None:
        if not data:
            raise ValueError(
                'Could not retrieve transaction.'
                ' Either it is invalid or might be in archive node.'
            )

    def get_transaction(self, transaction_hash: bytes) -> ITransactionData:
        """Obtain transaction object by hash."""
        data = self._web3.eth.get_transaction(HexBytes(transaction_hash))
        self._ensure_transaction_not_null(data)
        return web3_tx_to_matic_tx(data)

    def get_transaction_receipt(
        self, transaction_hash: bytes, timeout: int = 120
    ) -> ITransactionReceipt:
        """Get receipt for transaction."""
        data = self._web3.eth.wait_for_transaction_receipt(
            HexBytes(transaction_hash), timeout
        )
        self._ensure_transaction_not_null(data)
        return web3_receipt_to_matic_receipt(data)

    def get_block(
        self,
        block_hash_or_block_number: Literal['latest', 'earliest', 'pending']
        | bytes
        | HexBytes
        | int,
    ) -> IBlock:
        """Get block (with raw transaction data) by hash or number."""
        if isinstance(block_hash_or_block_number, bytes):
            block_hash_or_block_number = HexBytes(block_hash_or_block_number)
        data: Any = self._web3.eth.get_block(block_hash_or_block_number)
        return IBlock(
            size=data.size,
            difficulty=data.difficulty,
            total_difficulty=data.totalDifficulty,
            uncles=data.uncles,
            number=data.number,
            hash=data.hash,
            parent_hash=data.parentHash,
            nonce=data.nonce,
            sha3_uncles=data.sha3Uncles,
            logs_bloom=data.logsBloom,
            transactions_root=data.transactionsRoot,
            state_root=data.stateRoot,
            receipts_root=data.receiptsRoot,
            miner=data.miner,
            extra_data=data.proofOfAuthorityData,
            gas_limit=data.gasLimit,
            gas_used=data.gasUsed,
            timestamp=data.timestamp,
            # base_fee_per_gas=data.baseFeePerGas,
            transactions=data.transactions,
        )

    def get_block_with_transaction(
        self,
        block_hash_or_block_number: Literal['latest', 'earliest', 'pending']
        | bytes
        | HexBytes
        | int,
    ) -> IBlockWithTransaction:
        """Get block (with decoded transaction data) by hash or number."""
        if isinstance(block_hash_or_block_number, bytes):
            block_hash_or_block_number = HexBytes(block_hash_or_block_number)
        data: Any = self._web3.eth.get_block(block_hash_or_block_number, True)
        return IBlockWithTransaction(
            size=data.size,
            difficulty=data.difficulty,
            total_difficulty=data.totalDifficulty,
            uncles=data.uncles,
            number=data.number,
            hash=data.hash,
            parent_hash=data.parentHash,
            nonce=data.nonce,
            sha3_uncles=data.sha3Uncles,
            logs_bloom=data.logsBloom,
            transactions_root=data.transactionsRoot,
            state_root=data.stateRoot,
            receipts_root=data.receiptsRoot,
            miner=data.miner,
            extra_data=data.proofOfAuthorityData,
            gas_limit=data.gasLimit,
            gas_used=data.gasUsed,
            timestamp=data.timestamp,
            # base_fee_per_gas=data.baseFeePerGas,
            transactions=list(map(web3_tx_to_matic_tx, data.transactions)),
        )

    def send_rpc_request(self, request: IJsonRpcRequestPayload):
        """Perform arbitrary RPC request."""
        return self._web3.provider.make_request(
            cast(RPCEndpoint, request['method']), request['params']
        )

    def encode_parameters(self, params: Sequence[Any], types: Sequence[Any]):
        """Encode ABI parameters according to schema."""
        return encode_abi(types, params)

    def decode_parameters(self, binary_data: bytes, types: Sequence[Any]):
        """Decode binary data to ABI parameters according to schema."""
        return decode_abi(types, binary_data)

    def etherium_sha3(self, types: Iterable[str], values: Iterable[Any]) -> bytes:
        """Calculate solidity keccak hash of given values (encoded as types)."""
        return self._web3.solidityKeccak(types, values)
