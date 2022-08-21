from __future__ import annotations

from typing import Any, Generic, TypeVar, cast

from eth_typing import HexAddress

import matic
from matic.abstracts import BaseContract, BaseContractMethod, BaseWeb3Client
from matic.exceptions import (
    AllowedOnChildException,
    AllowedOnRootException,
    EIP1559NotSupportedException,
)
from matic.json_types import (
    IBaseClientConfig,
    ITransactionOption,
    ITransactionRequestConfig,
    ITransactionWriteResult,
)
from matic.utils.web3_side_chain_client import Web3SideChainClient

_C = TypeVar('_C', bound=IBaseClientConfig)


class BaseToken(Generic[_C]):
    """Base class for all tokens."""

    _contract: BaseContract | None = None

    def __init__(
        self,
        address: HexAddress,
        is_parent: bool,
        name: str,
        client: Web3SideChainClient[_C],
        bridge_type: str | None = None,
    ):
        self.address = address
        self.is_parent = is_parent
        self.name = name
        self.bridge_type = bridge_type
        self.client = client

    @property
    def contract(self) -> BaseContract:
        """Contract object."""
        if self._contract:
            return self._contract

        abi = self.client.get_abi(self.name, self.bridge_type)
        self._contract = self._get_contract(self.is_parent, self.address, abi)
        assert self._contract
        return self._contract

    def _check_option(
        self, option: ITransactionOption | None = None
    ) -> ITransactionOption:
        if option is not None:
            return option

        return cast(ITransactionOption, {})

    def method(self, method_name: str, *args: Any) -> Any:
        """Call arbitrary JSON-RPC method."""
        return self.contract.method(method_name, *args)

    def process_write(
        self,
        method: BaseContractMethod,
        option: ITransactionOption | None = None,
        private_key: str | None = None,
    ) -> ITransactionWriteResult:
        """Perform write (modifying) operation.

        Args:
            method: Method instance (with arguments passed on instantiation)
            option: Additional parameters.
                May contain special key ``return_transaction`` (see Returns section)
            private_key: Sender private key
                (may be missing, if your provider supports implicit tx signing)

        Returns:
            ITransactionWriteResult if actual write was performed;
                ITransactionRequestConfig if `return_transaction=True`.
                (builds the final transaction dictionary and returns it).
        """
        return_tx = bool(option and option.pop('return_transaction', False))
        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=method,
            is_parent=self.is_parent,
        )

        matic.logger.info('process write config: %s', config)
        return method.write(config, private_key, return_tx)

    def send_transaction(
        self,
        option: ITransactionOption | None = None,
        private_key: str | None = None,
    ) -> ITransactionWriteResult:
        """Sign and send the transaction."""
        is_parent = self.is_parent
        client = self.get_client(is_parent)

        return_tx = bool(option and option.pop('return_transaction', False))
        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=None,
            is_parent=self.is_parent,
        )

        matic.logger.info('process write config: %s', config)

        return client.write(config, private_key, return_tx)

    def read_transaction(self, option: ITransactionOption | None = None) -> Any:
        """Send read (non-modifying) transaction without RPC method.

        Args:
            option: Additional parameters.
                May contain special key ``return_transaction`` (see Returns section)

        Returns:
            ITransactionWriteResult if actual write was performed;
                ITransactionRequestConfig if `return_transaction=True`.
                (builds the final transaction dictionary and returns it).
        """
        is_parent = self.is_parent
        client = self.get_client(is_parent)

        return_tx = bool(option and option.pop('return_transaction', False))
        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=None,
            is_parent=self.is_parent,
        )

        matic.logger.info('process read config: %s', config)
        return client.read(config, return_tx)

    def process_read(
        self, method: BaseContractMethod, option: ITransactionOption | None = None
    ) -> Any:
        """Perform read (non-modifying) operation.

        Args:
            method: Method instance (with arguments passed on instantiation)
            option: Additional parameters.
                May contain special key ``return_transaction`` (see Returns section)

        Returns:
            ITransactionWriteResult if actual write was performed;
                ITransactionRequestConfig if `return_transaction=True`.
                (builds the final transaction dictionary and returns it).
        """
        return_tx = bool(option and option.pop('return_transaction', False))
        config = self.create_transaction_config(
            tx_config=option,
            is_write=False,
            method=method,
            is_parent=self.is_parent,
        )
        matic.logger.info('read tx config created: %s', config)

        return method.read(config, return_tx)

    def get_client(self, is_parent: bool) -> BaseWeb3Client:
        """Get web3 client instance."""
        return self.client.parent if is_parent else self.client.child

    def _get_contract(
        self, is_parent: bool, token_address: HexAddress, abi: dict[str, Any]
    ) -> BaseContract:
        client = self.get_client(is_parent)
        return client.get_contract(token_address, abi)

    def create_transaction_config(
        self,
        tx_config: ITransactionRequestConfig | None,
        method: BaseContractMethod | None,
        is_parent: bool,
        is_write: bool,
    ) -> ITransactionRequestConfig:
        """Fill in missing fields in transaction request.

        Warning: this method may raise if your transaction cannot be executed,
            pass ``gas_limit`` to prevent it from happening.
        """
        if is_parent:
            default_config = (  # type: ignore[attr-defined]
                self.client.config.get('parent') or {}
            ).get('default_config')
        else:
            default_config = (  # type: ignore[attr-defined]
                self.client.config.get('child') or {}
            ).get('default_config')

        merged_config = dict(default_config or {})
        merged_config.update(tx_config or {})

        tx_config = cast(ITransactionRequestConfig, merged_config)

        client = self.get_client(is_parent)
        matic.logger.info(
            'tx_config=%s, is_parent=%s, is_write=%s', tx_config, is_parent, is_write
        )

        def estimate_gas(config: ITransactionRequestConfig) -> int:
            if method:
                config.pop('value', None)  # already registered on method => ignored
                return method.estimate_gas(config)
            else:
                return client.estimate_gas(config)

        if not is_write:
            return tx_config

        is_eip_1559_supported = self.client.is_eip_1559_supported(is_parent)
        is_max_fee_provided = tx_config.get('max_fee_per_gas') or tx_config.get(
            'max_priority_fee_per_gas'
        )

        if not is_eip_1559_supported and is_max_fee_provided:
            raise EIP1559NotSupportedException

        if not tx_config.get('gas_limit'):
            tx_config['gas_limit'] = estimate_gas(tx_config)

        if not tx_config.get('nonce'):
            tx_config['nonce'] = client.get_transaction_count(
                tx_config['from'], 'pending'
            )
        tx_config.setdefault('chain_id', client.chain_id)

        return tx_config

    def transfer_erc_20(
        self,
        to: str,
        amount: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer ERC-20 token."""
        method = self.contract.method('transfer', to, amount)
        return self.process_write(method, option, private_key)

    def transfer_erc_721(
        self,
        from_: str,
        to: str,
        token_id: int,
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer ERC-721 token."""
        method = self.contract.method('transferFrom', from_, to, token_id)
        return self.process_write(method, option, private_key)

    def check_for_root(self) -> None:
        """Assert that method is called on parent chain instance."""
        if not self.is_parent:
            raise AllowedOnRootException

    def check_for_child(self) -> None:
        """Assert that method is called on child chain instance."""
        if self.is_parent:
            raise AllowedOnChildException

    def transfer_erc_1155(
        self,
        from_: str,
        to: str,
        amount: int,
        token_id: int,
        data: bytes | None = b'',
        private_key: str | None = None,
        option: ITransactionOption | None = None,
    ):
        """Transfer ERC-1155 token."""
        method = self.contract.method(
            'safeTransferFrom',
            from_,
            to,
            token_id,
            amount,
            data or b'',
        )
        return self.process_write(method, option, private_key)
