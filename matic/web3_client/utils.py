"""Conversion utils: web3 structures to matic."""

from __future__ import annotations

from typing import Any

from web3 import Web3

from matic.json_types import (
    ILog,
    ITransactionData,
    ITransactionReceipt,
    ITransactionRequestConfig,
)


def matic_tx_request_config_to_web3(data: ITransactionRequestConfig | None = None):
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
    return {k: v for k, v in prepared.items() if v is not None}


def web3_log_to_matic_log(log: Any) -> ILog:
    """Log: web3 to matic."""
    return ILog(
        address=log.get('address'),
        data=log.get('data'),
        topics=log.get('topics'),
        log_index=log.get('logIndex'),
        transaction_hash=log.get('transactionHash'),
        transaction_index=log.get('transactionIndex'),
        block_hash=log.get('blockHash'),
        block_number=log.get('blockNumber'),
        removed=log.get('removed'),
    )


def web3_receipt_to_matic_receipt(receipt: Any) -> ITransactionReceipt:
    """Transaction receipt: web3 to matic."""
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
        events=receipt.get('events', []),
        logs=list(map(web3_log_to_matic_log, receipt.get('logs', []))),
        logs_bloom=receipt.get('logsBloom'),
        root=receipt.get('root'),
        type=receipt.get('type'),
    )


def web3_tx_to_matic_tx(tx) -> ITransactionData:
    """Transaction: web3 to matic."""
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
