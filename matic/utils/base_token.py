from __future__ import annotations

from dataclasses import asdict
from typing import cast

from matic.abstracts import BaseContract, BaseContractMethod
from matic.exceptions import (
    AllowedOnChildException,
    AllowedOnRootException,
    EIP1559NotSupportedException,
)
from matic.json_types import (
    IContractInitParam,
    ITransactionOption,
    ITransactionRequestConfig,
    ITransactionWriteResult,
    POSERC1155TransferParam,
)
from matic.utils.web3_side_chain_client import Web3SideChainClient

# import { Web3SideChainClient } from "./web3_side_chain_client"
# import { BaseContractMethod, BaseContract, BaseWeb3Client } from "../abstracts"
# import {  merge } from "../utils"
# import { promiseResolve } from "./promise_resolve"
# import { ERROR_TYPE } from "../enums"
# import { POSERC1155TransferParam, TYPE_AMOUNT } from "../types"
# import { ErrorHelper } from "./error_helper"

# export interface ITransactionConfigParam {
#     tx_config: ITransactionRequestConfig
#     method?: BaseContractMethod
#     is_write?: boolean
#     is_parent?: boolean
# }


class BaseToken:
    _contract: BaseContract | None = None

    def __init__(
        self,
        contract_param: IContractInitParam,
        client: Web3SideChainClient,
    ):
        self.contract_param = contract_param
        self.client = client

    @property
    def contract(self) -> BaseContract:
        if self._contract:
            return self._contract

        abi = self.client.get_ABI(
            self.contract_param.name,
            self.contract_param.bridge_type,
        )
        self._contract = self._get_contract(
            self.contract_param.is_parent,
            self.contract_param.address,
            abi,
        )
        assert self._contract
        return self._contract

    def process_write(
        self, method: BaseContractMethod, option: ITransactionOption | None = None
    ) -> ITransactionWriteResult | ITransactionRequestConfig:
        self.client.logger.info('process write')
        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=method,
            is_parent=self.contract_param.is_parent,
        )

        self.client.logger.info('process write config')
        if option and option.get('return_transaction', False):
            return {
                **config,
                'data': method.encode_ABI(),
                'to': method.address,
            }

        return method.write(config)

    def send_transaction(
        self, option: ITransactionOption | None = None
    ) -> ITransactionWriteResult | ITransactionRequestConfig:
        is_parent = self.contract_param.is_parent
        client = self.get_client(is_parent)
        client.logger.info('process write')

        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=None,
            is_parent=self.contract_param.is_parent,
        )

        client.logger.info('process write config')
        if option and option.get('return_transaction', False):
            return config

        return client.write(config)

    def read_transaction(
        self, option: ITransactionOption | None = None
    ) -> ITransactionWriteResult | ITransactionRequestConfig:
        is_parent = self.contract_param.is_parent
        client = self.get_client(is_parent)
        client.logger.info('process read')

        config = self.create_transaction_config(
            tx_config=option,
            is_write=True,
            method=None,
            is_parent=self.contract_param.is_parent,
        )

        client.logger.info('write tx config created')
        if option and option.get('return_transaction', False):
            return config

        return client.read(config)

    def process_read(
        self, method: BaseContractMethod, option: ITransactionOption | None = None
    ):
        self.client.logger.info('process read')
        config = self.create_transaction_config(
            tx_config=option,
            is_write=False,
            method=method,
            is_parent=self.contract_param.is_parent,
        )
        self.client.logger.info('read tx config created')

        if option and option.get('return_transaction', False):
            assert self.contract
            return {**config, 'data': method.encode_ABI(), 'to': self._contract.address}

        return method.read(config)

    def get_client(self, is_parent: bool):
        if is_parent:
            return self.client.parent
        return self.client.child

    def _get_contract(self, is_parent, token_address, abi):
        client = self.get_client(is_parent)
        return client.get_contract(token_address, abi)

    @property
    def parent_default_config(self):
        return getattr(self.client.config.parent, 'default_config', None)

    @property
    def child_default_config(self):
        return getattr(self.client.config.child, 'default_config', None)

    def create_transaction_config(
        self,
        tx_config: ITransactionRequestConfig | None,
        method: BaseContractMethod | None,
        is_parent: bool,
        is_write: bool,
    ) -> ITransactionRequestConfig:
        default_config = (
            self.parent_default_config if is_parent else self.child_default_config
        )
        default_config_dict = asdict(default_config) if default_config else {}
        if from_ := default_config_dict.pop('from_', None):
            default_config_dict['from'] = from_

        tx_config = cast(
            ITransactionRequestConfig, default_config_dict | (tx_config or {})
        )

        client = self.client.parent if is_parent else self.client.child
        client.logger.info(
            'tx_config=%s, is_parent=%s, is_write=%s', tx_config, is_parent, is_write
        )

        def estimate_gas(config: ITransactionRequestConfig) -> int:
            return (
                method.estimate_gas(config) if method else client.estimate_gas(config)
            )

        # tx_config['chain_id'] = to_hex(tx_config['chain_id']) as any
        if not is_write:
            return tx_config

        is_EIP_1559_supported = self.client.is_EIP_1559_supported(is_parent)
        is_max_fee_provided = tx_config.get('max_fee_per_gas') or tx_config.get(
            'max_priority_fee_per_gas'
        )

        if not is_EIP_1559_supported and is_max_fee_provided:
            raise EIP1559NotSupportedException
        tx_config.setdefault(
            'gas_limit',
            estimate_gas(
                ITransactionRequestConfig(
                    {'from': tx_config['from'], 'value': tx_config['value']}
                )
            ),
        )

        tx_config.setdefault(
            'nonce', client.get_transaction_count(tx_config['from'], 'pending')
        )
        tx_config.setdefault('chain_id', client.chain_id)

        client.logger.info('options filled')

        return tx_config

    def transfer_ERC_20(
        self, to: bytes, amount: int, option: ITransactionOption | None = None
    ):
        method = self.contract.method('transfer', to, amount)
        option = option or {}
        option['value'] = amount
        return self.process_write(method, option)

    def transfer_ERC_721(
        self, from_: bytes, to: bytes, token_id: int, option: ITransactionOption
    ):
        method = self.contract.method('transferFrom', from_, to, token_id)
        return self.process_write(method, option)

    def check_for_root(self) -> None:
        if not self.contract_param.is_parent:
            raise AllowedOnRootException

    def check_for_child(self) -> None:
        if self.contract_param.is_parent:
            raise AllowedOnChildException

    def transfer_ERC_1155(
        self, param: POSERC1155TransferParam, option: ITransactionOption
    ):
        method = self.contract.method(
            'safeTransferFrom',
            param.from_,
            param.to,
            param.token_id,
            param.amount,
            param.data or '0x',
        )
        return self.process_write(method, option)
