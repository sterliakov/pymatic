from __future__ import annotations

from typing import Any

from web3 import Web3

from matic.json_types import ITransactionRequestConfig

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
        'gas': config.get('gas_limit'),
        'gas_price': config.get('gas_price'),
        'nonce': config.get('nonce'),
        'to': config.get('to'),
        'value': config.get('value'),
        'max_fee_per_gas': config.get('max_fee_per_gas'),
        'max_priority_fee_per_gas': config.get('max_priority_fee_per_gas'),
        'type': Web3.toHex(type_) if (type_ := config.get('type')) else None,
        'hardfork': config.get('hardfork'),
    }
    return {k: v for k, v in prepared.items() if v is not None}


def web3_receipt_to_matic_receipt(receipt: Any):
    return {
        'block_hash': receipt.get('block_hash'),
        'block_number': receipt.get('block_number'),
        'contract_address': receipt.get('contract_address'),
        'cumulative_gas_used': receipt.get('cumulative_gas_used'),
        'from': receipt.get('from'),
        'gas_used': receipt.get('gas_used'),
        'status': receipt.get('status'),
        'to': receipt.get('to'),
        'transaction_hash': receipt.get('transaction_hash'),
        'transaction_index': receipt.get('transaction_index'),
        'events': receipt.get('events'),
        'logs': receipt.get('logs'),
        'logs_bloom': receipt.get('logs_bloom'),
        'root': receipt.get('root'),
        'type': receipt.get('type'),
    }


def web3_tx_to_matic_tx(tx):
    matic_tx = dict(tx)
    matic_tx['transaction_hash'] = tx.get('hash')
    return matic_tx
