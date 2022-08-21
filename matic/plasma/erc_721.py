from __future__ import annotations

from typing import Callable

from eth_typing import HexAddress

from matic.abstracts import BaseContract
from matic.constants import PlasmaLogEventSignature
from matic.json_types import (
    IPlasmaClientConfig,
    IPlasmaContracts,
    ITransactionOption,
    ITransactionWriteResult,
)
from matic.plasma.plasma_token import PlasmaToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class ERC721(PlasmaToken):
    """ERC-721-compliant token on plasma bridge."""

    WITHDRAW_EXIT_SIGNATURE = PlasmaLogEventSignature.ERC_721_WITHDRAW_EVENT_SIG
    """Withdraw event signature, used for exit methods."""

    def __init__(
        self,
        token_address: HexAddress,
        is_parent: bool,
        client: Web3SideChainClient[IPlasmaClientConfig],
        contracts: Callable[[], IPlasmaContracts],
    ):
        super().__init__(
            address=token_address,
            is_parent=is_parent,
            name='ChildERC721',
            client=client,
            get_helper_contracts=contracts,
        )

    @property
    def predicate(self) -> BaseContract:
        """Get predicate contract for token."""
        return self._fetch_predicate(
            'erc721Predicate',
            'ERC721Predicate',
            self.client.config.get('erc_721_predicate'),
        )

    def get_tokens_count(
        self, user_address: HexAddress, option: ITransactionOption | None = None
    ) -> int:
        """Get tokens count for the user."""
        method = self.contract.method('balanceOf', user_address)
        return self.process_read(method, option)

    def get_token_id_at_index_for_user(
        self,
        index: int,
        user_address: HexAddress,
        option: ITransactionOption | None = None,
    ) -> int:
        """Returns token id on supplied index for user."""
        method = self.contract.method('tokenOfOwnerByIndex', user_address, index)
        return self.process_read(method, option)

    def safe_deposit(
        self,
        token_id: int,
        user_address: HexAddress,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Perform safeTransferFrom."""
        self.check_for_root()

        method = self.contract.method(
            'safeTransferFrom',
            user_address,
            self.get_helper_contracts().deposit_manager.address,
            token_id,
        )
        return self.process_write(method, option, private_key)

    def withdraw_start(
        self,
        token_id: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Initialize withdrawal process."""
        self.check_for_child()

        method = self.contract.method('withdraw', token_id)
        return self.process_write(method, option, private_key)

    def transfer(
        self,
        token_id: int,
        from_: HexAddress,
        to: HexAddress,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Perform transfer to another address."""
        return self.transfer_erc_721(from_, to, token_id, private_key, option)

    def get_all_tokens(
        self, user_address: HexAddress, limit: int | None = None
    ) -> list[int]:
        """Get all token ids that belong to the given user."""
        if limit is None:
            limit = self.get_tokens_count(user_address)
        # TODO: should be async

        return [
            self.get_token_id_at_index_for_user(i, user_address) for i in range(limit)
        ]
