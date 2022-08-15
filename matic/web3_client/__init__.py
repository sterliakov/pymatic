from __future__ import annotations

from logging import Logger
from typing import Any, Iterable, Sequence

from eth_abi import decode_abi, encode_abi
from web3 import Web3

from matic.abstracts import BaseContract, BaseContractMethod, BaseWeb3Client
from matic.json_types import (
    IBlock,
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
    def __init__(self, address: str, logger: Logger, method: Any, client=None) -> None:
        super().__init__(address, logger, method)
        self.method = method
        self.address = address
        self.client = client

    @staticmethod
    def to_hex(value):
        # FIXME: not needed
        return Web3.toHex(value) if value is not None else value

    def read(self, tx: ITransactionRequestConfig | None = None):
        self.logger.debug('sending tx with config %s', tx)
        return self.method.call(matic_tx_request_config_to_web3(tx))

    def write(
        self,
        tx: ITransactionRequestConfig,
        private_key: str | None = None,
    ) -> TransactionWriteResult:
        web3_tx = matic_tx_request_config_to_web3(tx)

        if private_key:
            tx_prep = self.method.build_transaction(web3_tx)
            print('Prepared tx: ', tx_prep)
            tx_signed = self.client._web3.eth.account.sign_transaction(
                tx_prep, private_key
            )
            res = self.client._web3.eth.send_raw_transaction(tx_signed.rawTransaction)
        else:
            res = self.client._web3.eth.send_transaction(web3_tx)

        return TransactionWriteResult(res, self.client)

    def estimate_gas(self, tx: ITransactionRequestConfig) -> int:
        return self.method.estimate_gas(matic_tx_request_config_to_web3(tx))

    def encode_ABI(self):
        abi = [e['type'] for e in self.method.abi['inputs']]
        return encode_abi(abi, self.method.args)


class Web3Contract(BaseContract):
    def __init__(self, address: str, contract, logger: Logger, client=None):
        super().__init__(address, logger)
        self.contract = contract
        self.client = client

    def method(self, method_name: str, *args):
        self.logger.debug('method_name %s; args method %s', method_name, args)
        return EthMethod(
            self.address,
            self.logger,
            self.contract.get_function_by_name(method_name)(*args),
            self.client,
        )


class Web3Client(BaseWeb3Client):
    _web3: Web3

    def __init__(self, provider: Any, logger: Logger):
        from web3.middleware import geth_poa_middleware

        super().__init__(provider, logger)
        self._web3 = Web3(provider)
        self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def read(self, config: ITransactionRequestConfig):
        return self._web3.eth.call(matic_tx_request_config_to_web3(config))

    def write(self, config: ITransactionRequestConfig):
        return TransactionWriteResult(
            self._web3.eth.send_transaction(matic_tx_request_config_to_web3(config)),
            self,
        )

    def get_contract(self, address: str, abi: dict[str, Any]):
        cont = self._web3.eth.contract(abi=abi, address=address)
        return Web3Contract(address, cont, self.logger, self)

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

    def get_transaction_receipt(
        self, transaction_hash: bytes, timeout: int = 120
    ) -> ITransactionReceipt:
        data = self._web3.eth.wait_for_transaction_receipt(transaction_hash, timeout)
        self._ensure_transaction_not_null(data)
        return web3_receipt_to_matic_receipt(data)

    def get_block(self, block_hash_or_block_number):
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

    def get_block_with_transaction(self, block_hash_or_block_number):
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

    def send_RPC_request(self, request: IJsonRpcRequestPayload):
        return self._web3.provider.make_request(request['method'], request['params'])

    def encode_parameters(self, params: Sequence[Any], types: Sequence[Any]):
        return encode_abi(types, params)

    def decode_parameters(self, binary_data: bytes, types: Sequence[Any]):
        return decode_abi(types, binary_data)

    def etherium_sha3(self, types: Iterable[str], values: Iterable[Any]) -> bytes:
        return self._web3.solidityKeccak(types, values)


def setup():
    import matic
    import matic.utils

    matic.utils.Web3Client = Web3Client
