from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from eth_typing import HexAddress

from matic.abstracts import BaseContract
from matic.json_types import (
    IPlasmaClientConfig,
    IPlasmaContracts,
    ITransactionOption,
    ITransactionWriteResult,
)
from matic.plasma.contracts import ErcPredicate
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class PlasmaToken(ABC, BaseToken[IPlasmaClientConfig]):
    """Base class for all tokens based on plasma bridge protocol."""

    _predicate: BaseContract | None = None
    WITHDRAW_EXIT_SIGNATURE: bytes
    """Withdraw event signature, used for exit methods."""

    def __init__(
        self,
        address: HexAddress,
        is_parent: bool,
        name: str,
        client: Web3SideChainClient[IPlasmaClientConfig],
        get_helper_contracts: Callable[[], IPlasmaContracts],
    ):
        super().__init__(
            address=address,
            is_parent=is_parent,
            name=name,
            bridge_type='plasma',
            client=client,
        )
        self.get_helper_contracts = get_helper_contracts

    def _fetch_predicate(
        self,
        method_name: str,
        contract_name: str,
        predicate_address: HexAddress | None = None,
    ) -> BaseContract:
        """Get predicate contract instance."""
        if not self._predicate:
            if predicate_address:
                address = predicate_address
            else:
                address = (
                    self.get_helper_contracts()
                    .registry.contract.method(method_name)
                    .read()
                )

            self._predicate = ErcPredicate(self.client, address, contract_name).contract

        return self._predicate

    def withdraw_exit(
        self, private_key: str | None = None, option: ITransactionOption | None = None
    ) -> ITransactionWriteResult:
        """Complete withdraw process."""
        return self.get_helper_contracts().withdraw_manager.withdraw_exit(
            self.address, private_key, option
        )

    @property
    @abstractmethod
    def predicate(self) -> BaseContract:
        """Get predicate contract for token."""
        ...

    def _withdraw_confirm(
        self,
        burn_tx_hash: bytes,
        is_fast: bool,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        self.check_for_root()
        # This is my attempt to fix, because the upstream JS implementation is wrong.
        payload = self.get_helper_contracts().exit_util.build_payload_for_exit(
            burn_tx_hash,
            0,
            self.WITHDRAW_EXIT_SIGNATURE,
            is_fast,
        )
        method = self.predicate.method('startExitWithBurntTokens', payload)
        return self.process_write(method, option, private_key)

    def withdraw_confirm(
        self,
        burn_tx_hash: bytes,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Continue withdraw process."""
        return self._withdraw_confirm(burn_tx_hash, False, private_key, option)

    def withdraw_confirm_faster(
        self,
        burn_tx_hash: bytes,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Continue withdraw process with fast proof."""
        return self._withdraw_confirm(burn_tx_hash, True, private_key, option)
