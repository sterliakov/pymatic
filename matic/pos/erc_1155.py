from __future__ import annotations

from typing import Sequence

from matic.constants import LogEventSignature
from matic.json_types import (
    IPOSERC1155Address,
    ITransactionOption,
    POSERC1155DepositBatchParam,
    POSERC1155DepositParam,
    POSERC1155TransferParam,
)
from matic.pos.pos_token import POSToken
from matic.utils import to_hex

# import { IPOSClientConfig, ITransactionOption } from "../interfaces"
# import { Converter, promiseResolve, Web3SideChainClient } from "../utils"
# import { POSToken } from "./pos_token"
# import { LogEventSignature } from "../enums"
# import { IPOSContracts, IPOSERC1155Address } from "../interfaces"
# import { POSERC1155DepositBatchParam, POSERC1155DepositParam, POSERC1155TransferParam, TYPE_AMOUNT } from ".."


class ERC1155(POSToken):
    mintable_predicate_address: str
    CONTRACT_NAME: str = 'ChildERC1155'

    @property
    def address_config(self) -> IPOSERC1155Address:
        return getattr(self.client.config, 'erc_1155', {}) or {}

    def _get_address(self, value: str):
        addr = self.address_config.get(value)
        if addr is not None:
            return addr
        return self.client.get_config(value)

    def get_balance(
        self, user_address: str, token_id: int, option: ITransactionOption | None = None
    ) -> int:
        """Get balance of a user for supplied token."""
        method = self.contract.method(
            'balanceOf',
            user_address,
            to_hex(token_id),
        )
        return self.process_read(method, option)

    def is_approved_all(
        self, user_address: str, option: ITransactionOption | None = None
    ):
        """Check if a user is approved for all tokens."""
        self.check_for_root()

        method = self.contract.method(
            'isApprovedForAll', user_address, self.predicate_address
        )
        return self.process_read(method, option)

    def _approve_all(
        self, predicate_address: str, option: ITransactionOption | None = None
    ):
        self.check_for_root()
        method = self.contract.method('setApprovalForAll', predicate_address, True)
        return self.process_write(method, option)

    def approve_all(self, option: ITransactionOption | None = None):
        """Approve all tokens."""
        self.check_for_root()

        return self._approve_all(self.predicate_address, option)

    def approve_all_for_mintable(self, option: ITransactionOption | None = None):
        """Approve all tokens for mintable token."""
        self.check_for_root()
        address_path = 'Main.POSContracts.MintableERC1155PredicateProxy'
        return self._approve_all(self._get_address(address_path), option)

    def deposit(
        self, param: POSERC1155DepositParam, option: ITransactionOption | None = None
    ):
        """Deposit supplied amount of token for a user."""
        self.check_for_root()
        return self.deposit_many(
            POSERC1155DepositBatchParam(
                amounts=[param.amount],
                token_ids=[param.token_id],
                user_address=param.user_address,
                data=param.data,
            ),
            option,
        )

    def deposit_many(
        self,
        param: POSERC1155DepositBatchParam,
        option: ITransactionOption | None = None,
    ):
        """Deposit supplied amount of multiple token for user."""
        self.check_for_root()

        amount_in_ABI = self.client.parent.encode_parameters(
            [
                list(map(to_hex, param.token_ids)),
                list(map(to_hex, param.amounts)),
                param.data or b'',
            ],
            ['uint256[]', 'uint256[]', 'bytes'],
        )

        return self.root_chain_manager.deposit(
            param.user_address, self.contract_param.address, amount_in_ABI, option
        )

    def withdraw_start(
        self, token_id: int, amount: int, option: ITransactionOption | None = None
    ):
        """Start withdraw process by burning the required amount for a token."""
        self.check_for_child()

        method = self.contract.method(
            'withdrawSingle', to_hex(token_id), to_hex(amount)
        )
        return self.process_write(method, option)

    def withdraw_start_many(
        self,
        token_ids: Sequence[int],
        amounts: Sequence[int],
        option: ITransactionOption | None = None,
    ):
        """
        Start the withdraw process by burning the supplied amount of multiple token at a time.
        """
        self.check_for_child()

        method = self.contract.method(
            'withdrawBatch', list(map(to_hex, token_ids)), list(map(to_hex, amounts))
        )
        return self.process_write(method, option)

    def withdraw_exit(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        """Exit the withdraw process and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_POS(
            burn_transaction_hash, LogEventSignature.ERC_1155_TRANSFER, False, option
        )

    def withdraw_exit_faster(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        """Exit the withdraw process and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_POS(
            burn_transaction_hash, LogEventSignature.ERC_1155_TRANSFER, True, option
        )

    def withdraw_exit_many(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        """Exit the withdraw process for many burned transaction and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_POS(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            False,
            option,
        )

    def withdraw_exit_faster_many(
        self, burn_transaction_hash: bytes, option: ITransactionOption | None = None
    ):
        """Exit the withdraw process for many burned transaction and get the burned amount on root chain."""
        self.check_for_root()
        return self.withdraw_exit_POS(
            burn_transaction_hash,
            LogEventSignature.ERC_1155_BATCH_TRANSFER,
            True,
            option,
        )

    def is_withdraw_exited(self, tx_hash: bytes) -> bool:
        """Check if exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_1155_TRANSFER)

    def is_withdraw_exited_many(self, tx_hash: bytes) -> bool:
        """Check if batch exit has been completed for a transaction hash."""
        return self.is_withdrawn(tx_hash, LogEventSignature.ERC_1155_BATCH_TRANSFER)

    def transfer(
        self, param: POSERC1155TransferParam, option: ITransactionOption | None = None
    ):
        """Transfer the required amount of a token to another user."""
        return self.transfer_ERC_1155(param, option)
