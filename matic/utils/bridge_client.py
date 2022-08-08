from __future__ import annotations

from matic.json_types import IBaseClientConfig, IContractInitParam
from matic.pos.exit_util import ExitUtil
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient

# import { Web3SideChainClient } from "../utils";
# import { ExitUtil } from "../pos";
# import { BaseToken, utils } from "..";


class BridgeClient:
    # Options: 'testnet', 'mumbai'
    client: Web3SideChainClient
    exit_util: ExitUtil

    def __init__(self, config: IBaseClientConfig):
        self.client = Web3SideChainClient(config)

    def is_checkpointed(self, tx_hash: bytes) -> bool:
        return self.exit_util.is_checkpointed(tx_hash)

    def is_deposited(self, deposit_tx_hash: bytes) -> bool:
        client = self.client

        token = BaseToken(
            IContractInitParam(
                address=client.abi_manager.get_config(
                    'Matic.GenesisContracts.StateReceiver'
                ),
                is_parent=False,
                name='StateReceiver',
                bridge_type='genesis',
            ),
            client=client,
        )

        receipt = client.parent.get_transaction_receipt(deposit_tx_hash)
        last_state_id = token.process_read(token.contract.method('lastStateId'))

        event_signature = bytes.fromhex(
            '103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392'
        )
        try:
            target_log = next(
                log for log in receipt.logs if log.topics[0] == event_signature
            )
        except StopIteration:
            raise RuntimeError('StateSynced event not found')

        root_state_id = client.child.decode_parameters(
            target_log.topics[1], ['uint256']
        )[0]
        return last_state_id >= root_state_id
