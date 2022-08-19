from __future__ import annotations

from matic.json_types import ITransactionOption
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class RootChainManager(BaseToken):
    """Root chain manager handles common operations related to POS bridge withdrawal."""

    def __init__(self, client: Web3SideChainClient, address: str) -> None:
        super().__init__(
            address=address,
            name='RootChainManager',
            bridge_type='pos',
            is_parent=True,
            client=client,
        )

    def deposit(
        self,
        user_address: str,
        token_address: str,
        deposit_data: bytes,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Finish deposit operation.

        When token is approved, this is used to process "conversion". It may take 5-10
        minutes after this call to receive funds.

        Args:
            user_address: Receiving user address
            token_address: Address of contract defining token
            deposit_data: Pre-built binary data to send
            private_key: Receiving user PK
            option: Standard transaction option.
        """
        method = self.method('depositFor', user_address, token_address, deposit_data)
        return self.process_write(method, option, private_key)

    def exit(  # noqa: A003
        self,
        exit_payload: bytes,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Finish exit operation.

        Args:
            exit_payload: Pre-built binary data to send
            private_key: Sender PK
            option: Standard transaction option.
        """
        method = self.method('exit', exit_payload)
        return self.process_write(method, option, private_key)

    def is_exit_processed(self, exit_hash: bytes) -> bool:
        """Check if exit was already processed for given transaction."""
        method = self.method('processedExits', exit_hash)
        return self.process_read(method)
