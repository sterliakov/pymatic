from __future__ import annotations

from typing import Callable

from matic.json_types import IExitTransactionOption, IPOSContracts, ITransactionOption
from matic.pos.exit_util import ExitUtil
from matic.pos.root_chain_manager import RootChainManager
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class POSToken(BaseToken):
    """Base class for all tokens based on POS bridge protocol."""

    _predicate_address: str | None = None
    CONTRACT_NAME: str  # TODO: should be abstract
    BURN_EVENT_SIGNATURE: bytes  # TODO: should be abstract

    def __init__(
        self,
        token_address: str,
        is_parent: bool,
        client: Web3SideChainClient,
        get_pos_contracts: Callable[[], IPOSContracts],
    ) -> None:
        super().__init__(
            is_parent=is_parent,
            address=token_address,
            name=self.CONTRACT_NAME,
            bridge_type='pos',
            client=client,
        )
        self.get_pos_contracts = get_pos_contracts

    @property
    def root_chain_manager(self) -> RootChainManager:
        """Get RootChainManager instance."""
        return self.get_pos_contracts().root_chain_manager

    @property
    def exit_util(self) -> ExitUtil:
        """Get ExitUtil instance."""
        return self.get_pos_contracts().exit_util

    @property
    def predicate_address(self) -> str:
        """Memoise and get predicate address from root chain manager."""
        if self._predicate_address:
            return self._predicate_address

        token_type = self.root_chain_manager.method('tokenToType', self.address).read()

        if not token_type:
            raise ValueError('Invalid Token Type')

        predicate_address = self.root_chain_manager.method(
            'typeToPredicate', token_type
        ).read()

        self._predicate_address = predicate_address
        return predicate_address

    def is_withdrawn(self, tx_hash: bytes, event_signature: bytes) -> bool:
        """Check if transaction withdrawal was completed."""
        exit_hash = self.exit_util.get_exit_hash(tx_hash, 0, event_signature)
        return self.root_chain_manager.is_exit_processed(exit_hash)

    def is_withdrawn_on_index(
        self, tx_hash: bytes, index: int, event_signature: bytes
    ) -> bool:
        """Check if transaction withdrawal was completed on index."""
        exit_hash = self.exit_util.get_exit_hash(tx_hash, index, event_signature)
        return self.root_chain_manager.is_exit_processed(exit_hash)

    def withdraw_exit_pos(
        self,
        burn_tx_hash: bytes,
        event_signature: bytes,
        private_key: str | None = None,
        is_fast: bool = True,
        index: int = 0,
        *,
        option: IExitTransactionOption | None = None,
    ) -> None:
        """Base POS exit method, called by more specific implementations."""
        self.check_for_root()

        event_signature = (
            option.get('burn_event_signature') if option is not None else None
        ) or event_signature

        payload = self.exit_util.build_payload_for_exit(
            burn_tx_hash, index, event_signature, is_fast
        )
        return self.root_chain_manager.exit(payload, private_key, option)

    def withdraw_exit(
        self,
        burn_transaction_hash: bytes,
        private_key: str | None = None,
        option: IExitTransactionOption | None = None,
    ):
        """Complete withdraw process.

        This function should be called after checkpoint has been submitted
        for the block containing burn tx.

        This function fetches required blocks and builds proof using them.
        """
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            self.BURN_EVENT_SIGNATURE,
            private_key,
            False,
            option=option,
        )

    def withdraw_exit_faster(
        self,
        burn_transaction_hash: bytes,
        private_key: str | None = None,
        option: IExitTransactionOption | None = None,
    ):
        """Complete withdraw process.

        This function should be called after checkpoint has been submitted
        for the block containing burn tx.

        This function uses API to fetch proof data.
        """
        return self.withdraw_exit_pos(
            burn_transaction_hash,
            self.BURN_EVENT_SIGNATURE,
            private_key,
            True,
            option=option,
        )

    def is_withdraw_exited(self, tx_hash: bytes) -> bool:
        """Check if exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, self.BURN_EVENT_SIGNATURE)


class TokenWithApproveAll(POSToken):
    """This is a general token with common methods for ERC721 and ERC1155."""

    def is_approved_all(
        self, user_address: str, option: ITransactionOption | None = None
    ) -> bool:
        """Check if a user is approved for all tokens."""
        self.check_for_root()
        method = self.contract.method(
            'isApprovedForAll', user_address, self.predicate_address
        )
        return bool(self.process_read(method, option))

    def _approve_all(
        self,
        predicate_address: str,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        self.check_for_root()
        method = self.contract.method('setApprovalForAll', predicate_address, True)
        return self.process_write(method, option, private_key)

    def approve_all(
        self, private_key: str | None = None, option: ITransactionOption | None = None
    ):
        """Approve all tokens."""
        return self._approve_all(self.predicate_address, private_key, option)
