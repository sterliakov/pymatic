from __future__ import annotations

from typing import Any

from web3 import Web3

from matic.json_types import (
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
)

# import { ITransactionRequestConfig } from "@maticnetwork/maticjs"
# import Web3 from "web3"
# import { TransactionConfig } from "web3-core"

# FIXME: use .get


def matic_tx_request_config_to_web3(data: ITransactionRequestConfig | None = None):
    config: dict[str, Any] = dict(data or {})

    prepared = {
        'chain_id': Web3.toHex(chain_id)
        if (chain_id := config.get('chain_id'))
        else None,
        'data': config.get('data'),
        'from': config.get('from'),
        'gas': config.get('gasLimit'),
        'gas_price': config.get('gasPrice'),
        'nonce': config.get('nonce'),
        'to': config.get('to'),
        'value': config.get('value'),
        'max_fee_per_gas': config.get('maxFeePerGas'),
        'max_priority_fee_per_gas': config.get('maxPriorityFeePerGas'),
        'type': Web3.toHex(type_) if (type_ := config.get('type')) else None,
        'hardfork': config.get('hardfork'),
    }
    return {k: v for k, v in prepared.items() if v is not None}


def web3_receipt_to_matic_receipt(receipt: Any):
    return ITransactionReceipt(
        block_hash=receipt.get('blockHash'),
        block_number=receipt.get('blockNumber'),
        contract_address=receipt.get('contractAddress'),
        cumulative_gas_used=receipt.get('cumulativeGasUsed'),
        from_=receipt.get('from'),
        gas_used=receipt.get('gasUsed'),
        status=receipt.get('status'),
        to=receipt.get('to'),
        transaction_hash=receipt.get('transactionHash'),
        transaction_index=receipt.get('transactionIndex'),
        events=receipt.get('events'),
        logs=receipt.get('logs'),
        logs_bloom=receipt.get('logsBloom'),
        root=receipt.get('root'),
        type=receipt.get('type'),
    )


def web3_tx_to_matic_tx(tx):
    # matic_tx = dict(tx)
    # matic_tx['transaction_hash'] = matic_tx.pop('hash')
    # matic_tx['block_hash'] = matic_tx.pop('blockHash')
    return ITransactionData(
        transaction_hash=tx.hash,
        nonce=tx.nonce,
        block_hash=tx.blockHash,
        block_number=tx.blockNumber,
        transaction_index=tx.transactionIndex,
        from_=tx['from'],
        to=tx.to,
        value=tx.value,
        gas_price=tx.gasPrice,
        gas=tx.gas,
        input=tx.input,
    )
