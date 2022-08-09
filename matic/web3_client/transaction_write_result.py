from __future__ import annotations

from matic.json_types import ITransactionWriteResult
from matic.web3_client.utils import web3_receipt_to_matic_receipt


def do_nothing(*args, **kwargs):
    pass


# FIXME: bad
class TransactionWriteResult(ITransactionWriteResult):
    @property
    def receipt(self):
        receipt = self.client._web3.eth.wait_for_transaction_receipt(self.tx_hash)
        return web3_receipt_to_matic_receipt(receipt)

    @property
    def transaction_hash(self) -> bytes:
        return self.tx_hash

    def __init__(self, tx_hash: bytes, client):
        self.tx_hash = tx_hash
        self.client = client
