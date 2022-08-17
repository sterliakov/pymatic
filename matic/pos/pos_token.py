from __future__ import annotations

from typing import Callable

from matic.json_types import IContractInitParam, IPOSContracts, ITransactionOption
from matic.pos.exit_util import ExitUtil
from matic.pos.root_chain_manager import RootChainManager
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class POSToken(BaseToken):
    _predicate_address: str | None = None
    CONTRACT_NAME: str  # TODO: should be abstract

    def __init__(
        self,
        token_address: bytes,
        is_parent: bool,
        client: Web3SideChainClient,
        get_pos_contracts: Callable[[], IPOSContracts],
    ):
        super().__init__(
            IContractInitParam(  # FIXME: never, please
                is_parent=is_parent,
                address=token_address,
                name=self.CONTRACT_NAME,
                bridge_type='pos',
            ),
            client=client,
        )
        self.get_pos_contracts = get_pos_contracts

    @property
    def root_chain_manager(self) -> RootChainManager:
        return self.get_pos_contracts().root_chain_manager

    @property
    def exit_util(self) -> ExitUtil:
        return self.get_pos_contracts().exit_util

    @property
    def predicate_address(self) -> str:
        if self._predicate_address:
            return self._predicate_address

        token_type = self.root_chain_manager.method(
            'tokenToType', self.contract_param.address
        ).read()

        if not token_type:
            raise ValueError('Invalid Token Type')

        predicate_address = self.root_chain_manager.method(
            'typeToPredicate', token_type
        ).read()

        self._predicate_address = predicate_address
        return predicate_address

    def is_withdrawn(self, tx_hash: bytes, event_signature: bytes) -> bool:
        exit_hash = self.exit_util.get_exit_hash(tx_hash, 0, event_signature)
        return self.root_chain_manager.is_exit_processed(exit_hash)

    def is_withdrawn_on_index(
        self, tx_hash: bytes, index: int, event_signature: bytes
    ) -> bool:
        exit_hash = self.exit_util.get_exit_hash(tx_hash, index, event_signature)
        return self.root_chain_manager.is_exit_processed(exit_hash)

    def withdraw_exit_pos(
        self,
        burn_tx_hash: bytes,
        event_signature: bytes,
        private_key: str,
        is_fast: bool = True,
        option: ITransactionOption | None = None,
    ) -> None:
        payload = self.exit_util.build_payload_for_exit(
            burn_tx_hash, 0, event_signature, is_fast
        )
        return self.root_chain_manager.exit(payload, private_key, option)
