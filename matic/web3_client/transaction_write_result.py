from __future__ import annotations

from matic.json_types import ITransactionWriteResult
from matic.web3_client.utils import web3_receipt_to_matic_receipt


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
