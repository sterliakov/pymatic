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
    data: ITransactionRequestConfig | None = None,
) -> TxParams:
    """Transaction request: matic to web3."""
    config: dict[str, Any] = dict(data or {})
    type_ = config.get('type')
    prepared = {
        'chainId': config.get('chain_id'),
        'data': config.get('data'),
        'from': config.get('from'),
        'gas': config.get('gas_limit'),
        'gasPrice': config.get('gas_price'),
        'nonce': config.get('nonce'),
        'to': config.get('to'),
        'value': config.get('value'),
        'maxFeePerGas': config.get('max_fee_per_gas'),
        'maxPriorityFeePerGas': config.get('max_priority_fee_per_gas'),
        'type': Web3.toHex(type_) if type_ else None,
        'hardfork': config.get('hardfork'),
    }
    return cast(TxParams, {k: v for k, v in prepared.items() if v is not None})


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
