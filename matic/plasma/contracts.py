from __future__ import annotations

from typing import Iterable

from eth_typing import HexAddress

from matic.json_types import (
    IPlasmaClientConfig,
    ITransactionOption,
    ITransactionWriteResult,
)
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class DepositManager(BaseToken[IPlasmaClientConfig]):
    """Deposit manager for plasma bridge."""

    def __init__(
        self, client: Web3SideChainClient[IPlasmaClientConfig], address: HexAddress
    ) -> None:
        super().__init__(
            address=address,
            is_parent=True,
            name='DepositManager',
            client=client,
        )


class ErcPredicate(BaseToken[IPlasmaClientConfig]):
    """ERC predicate contract for plasma bridge."""

    def __init__(
        self,
        client: Web3SideChainClient[IPlasmaClientConfig],
        address: HexAddress,
        contract_name: str,
    ) -> None:
        super().__init__(
            is_parent=True,
            address=address,
            name=contract_name,
            client=client,
        )


class RegistryContract(BaseToken[IPlasmaClientConfig]):
    """Registry contract for plasma bridge."""

    def __init__(
        self, client: Web3SideChainClient[IPlasmaClientConfig], address: HexAddress
    ) -> None:
        super().__init__(
            address=address,
            is_parent=True,
            name='Registry',
            client=client,
        )


class WithdrawManager(BaseToken[IPlasmaClientConfig]):
    """Withdraw manager for plasma bridge."""

    def __init__(
        self, client: Web3SideChainClient[IPlasmaClientConfig], address: HexAddress
    ) -> None:
        super().__init__(
            address=address,
            is_parent=True,
            name='WithdrawManager',
            client=client,
        )

    def withdraw_exit(
        self,
        tokens: HexAddress | Iterable[HexAddress],
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ) -> ITransactionWriteResult:
        """Finish withdrawal process for given token(s)."""
        if isinstance(tokens, str):
            method = self.contract.method('processExits', tokens)
        else:
            method = self.contract.method('processExitsBatch', list(tokens))

        return self.process_write(method, option, private_key)
