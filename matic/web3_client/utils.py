"""Conversion utils: web3 structures to matic."""

from __future__ import annotations

from typing import Any, cast

from web3 import Web3
from web3.types import LogReceipt, TxData, TxParams, TxReceipt

from matic.json_types import (
    ILog,
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
)


def matic_tx_request_config_to_web3(
    config: ITransactionRequestConfig | None = None,
) -> TxParams:
    """Transaction request: matic to web3."""
    data: dict[str, Any] = dict(config or {})
    type_ = data.get('type')
    prepared = {
        'chainId': data.get('chain_id'),
        'data': data.get('data'),
        'from': data.get('from'),
        'gas': data.get('gas_limit'),
        'gasPrice': data.get('gas_price'),
        'nonce': data.get('nonce'),
        'to': data.get('to'),
        'value': data.get('value'),
        'maxFeePerGas': data.get('max_fee_per_gas'),
        'maxPriorityFeePerGas': data.get('max_priority_fee_per_gas'),
        'type': Web3.toHex(type_) if type_ else None,
        'hardfork': data.get('hardfork'),
    }
    return cast(TxParams, {k: v for k, v in prepared.items() if v is not None})


def web3_tx_request_config_to_matic(data: TxParams) -> ITransactionRequestConfig:
    """Transaction request: web3 to matic."""
    type_ = data.get('type')
    prepared = {
        'chain_id': data.get('chainId'),
        'data': data.get('data'),
        'from': data.get('from'),
        'gas_limit': data.get('gas'),
        'gas_price': data.get('gasPrice'),
        'nonce': data.get('nonce'),
        'to': data.get('to'),
        'value': data.get('value'),
        'max_fee_per_gas': data.get('maxFeePerGas'),
        'max_priority_fee_per_gas': data.get('maxPriorityFeePerGas'),
        'type': Web3.toHex(type_) if type_ else None,  # type: ignore
        'hardfork': data.get('hardfork'),
    }
    return cast(
        ITransactionRequestConfig, {k: v for k, v in prepared.items() if v is not None}
    )


def web3_log_to_matic_log(log: LogReceipt) -> ILog:
    """Log: web3 to matic."""
    return ILog(
        address=log['address'],
        data=log['data'],
        topics=log['topics'],
        log_index=log['logIndex'],
        transaction_hash=log['transactionHash'],
        transaction_index=log['transactionIndex'],
        block_hash=log['blockHash'],
        block_number=log['blockNumber'],
        removed=log['removed'],
    )


def web3_receipt_to_matic_receipt(receipt: TxReceipt) -> ITransactionReceipt:
    """Transaction receipt: web3 to matic."""
    return ITransactionReceipt(
        block_hash=receipt['blockHash'],
        block_number=receipt['blockNumber'],
        contract_address=receipt['contractAddress'],
        cumulative_gas_used=receipt['cumulativeGasUsed'],
        from_=receipt['from'],
        gas_used=receipt['gasUsed'],
        status=bool(receipt['status']) if 'status' in receipt else None,
        to=receipt['to'],
        transaction_hash=receipt['transactionHash'],
        transaction_index=receipt['transactionIndex'],
        # events=receipt.get('events', []),
        logs=list(map(web3_log_to_matic_log, receipt.get('logs', []))),
        logs_bloom=receipt['logsBloom'],
        root=receipt.get('root'),  # It is missing sometimes
        type=receipt.get('type'),  # type: ignore
    )


def web3_tx_to_matic_tx(tx: TxData) -> ITransactionData:
    """Transaction: web3 to matic."""
    return ITransactionData(
        transaction_hash=tx['hash'],
        nonce=tx['nonce'],
        block_hash=tx['blockHash'],
        block_number=tx['blockNumber'],
        transaction_index=tx['transactionIndex'],
        from_=tx['from'],
        to=tx['to'],
        value=tx['value'],
        gas_price=tx['gasPrice'],
        gas=tx['gas'],
        input=tx['input'],
    )
