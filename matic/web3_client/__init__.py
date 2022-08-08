from __future__ import annotations

from logging import Logger
from typing import Any, Sequence, cast

from eth_abi import decode_abi, encode_abi
from web3 import Web3

from matic.abstracts import BaseContract, BaseContractMethod, BaseWeb3Client
from matic.json_types import (
    IBlockWithTransaction,
    IJsonRpcRequestPayload,
    ITransactionReceipt,
    ITransactionRequestConfig,
)
from matic.web3_client.transaction_write_result import TransactionWriteResult
from matic.web3_client.utils import (
    matic_tx_request_config_to_web3,
    web3_receipt_to_matic_receipt,
    web3_tx_to_matic_tx,
)

# import {
#     BaseContractMethod, Logger, ITransactionRequestConfig
# } from "@maticnetwork/maticjs"
# import Web3 from "web3"
# import { TransactionObject, Tx } from "web3/eth/types"
# import { doNothing, TransactionWriteResult } from "../helpers"
# import { matic_tx_request_config_to_web3 } from "../utils"

# import { BaseContract } from "@maticnetwork/maticjs"
# import Contract from "web3/eth/contract"
# import { EthMethod } from "./eth_method"

# import { Web3Contract } from "./eth_contract"
# import Web3 from "web3"
# import { Transaction } from "web3/eth/types"
# import { AbstractProvider } from "web3-core"
# import { doNothing, TransactionWriteResult } from "../helpers"
# import {
#     BaseWeb3Client, IBlockWithTransaction, IJsonRpcRequestPayload,
#     IJsonRpcResponse, ITransactionRequestConfig, ITransactionData,
#     ITransactionReceipt, Logger, ERROR_TYPE, IError
# } from "@maticnetwork/maticjs"
# import {
#     matic_tx_request_config_to_web3, web3ReceiptToMaticReceipt, web3_tx_to_matic_tx
# } from "../utils"


class EthMethod(BaseContractMethod):
    def __init__(self, address: str, logger: Logger, method: Any) -> None:
        super().__init__(address, logger, method)
        self.method = method
        self.address = address
        print(self.method, self.method.args)

    @staticmethod
    def to_hex(value):
        return Web3.toHex(value) if value is not None else value

    def read(self, tx: ITransactionRequestConfig | None = None):
        self.logger.debug('sending tx with config %s', tx)
        return self.method.call(matic_tx_request_config_to_web3(tx))

    def write(self, tx: ITransactionRequestConfig) -> TransactionWriteResult:
        return TransactionWriteResult(
            self.method.send(matic_tx_request_config_to_web3(tx))
        )

    def estimate_gas(self, tx: ITransactionRequestConfig) -> int:
        print(matic_tx_request_config_to_web3(tx))
        return self.method.estimate_gas(matic_tx_request_config_to_web3(tx))

    def encode_ABI(self):
        return self.method.encode_ABI()


class Web3Contract(BaseContract):
    def __init__(self, address: str, contract, logger: Logger):
        super().__init__(address, logger)
        self.contract = contract

    def method(self, method_name: str, *args):
        self.logger.debug('method_name %s; args method %s', method_name, args)
        return EthMethod(
            self.address,
            self.logger,
            self.contract.get_function_by_name(method_name)(*args),
        )


class Web3Client(BaseWeb3Client):
    _web3: Web3

    def __init__(self, provider: Any, logger: Logger):
        super().__init__(provider, logger)
        print(provider)
        self._web3 = Web3(provider)

    def read(self, config: ITransactionRequestConfig):
        return self._web3.eth.call(matic_tx_request_config_to_web3(config))

    def write(self, config: ITransactionRequestConfig):
        return TransactionWriteResult(
            self._web3.eth.send_transaction(matic_tx_request_config_to_web3(config))
        )

    def get_contract(self, address: str, abi: dict[str, Any]):
        cont = self._web3.eth.contract(abi=abi, address=address)
        return Web3Contract(address, cont, self.logger)

    @property
    def gas_price(self) -> int:
        return self._web3.eth.gas_price

    def estimate_gas(self, config: ITransactionRequestConfig) -> int:
        return self._web3.eth.estimate_gas(matic_tx_request_config_to_web3(config))

    def get_transaction_count(self, address: str, block_number: int) -> int:
        return self._web3.eth.get_transaction_count(address, block_number)

    @property
    def chain_id(self):
        return self._web3.eth.chain_id

    def _ensure_transaction_not_null(self, data) -> None:
        if not data:
            raise ValueError(
                'Could not retrieve transaction.'
                ' Either it is invalid or might be in archive node.'
            )

    def get_transaction(self, transaction_hash: bytes):
        data = self._web3.eth.get_transaction(transaction_hash)
        self._ensure_transaction_not_null(data)
        return web3_tx_to_matic_tx(data)

    def get_transaction_receipt(self, transaction_hash: bytes) -> ITransactionReceipt:
        data = self._web3.eth.get_transaction_receipt(transaction_hash)
        self._ensure_transaction_not_null(data)
        return web3_receipt_to_matic_receipt(data)

    def get_block(self, block_hash_or_block_number):
        return self._web3.eth.get_block(block_hash_or_block_number)

    def get_block_with_transaction(self, block_hash_or_block_number):
        result = self._web3.eth.get_block(block_hash_or_block_number, True)
        block_data = cast(IBlockWithTransaction, result)
        block_data.transactions = list(
            map(web3_tx_to_matic_tx, block_data.transactions)
        )
        return block_data

    def send_RPC_request(self, request: IJsonRpcRequestPayload):
        return self._web3.provider.make_request(
            cast(dict[str, Any], request).pop('method'), request
        )

    def encode_parameters(self, params: Sequence[Any], types: Sequence[Any]):
        return encode_abi(types, params)

    def decode_parameters(self, binary_data: bytes, types: Sequence[Any]):
        return decode_abi(types, binary_data)

    def etherium_sha3(self, *value):
        return Web3.solidityKeccak(*value)


def setup():
    # sys.modules.pop('matic', None)
    # sys.modules.pop('matic.utils', None)

    import matic
    import matic.utils

    matic.utils.Web3Client = Web3Client
