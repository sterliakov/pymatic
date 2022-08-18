from __future__ import annotations

from matic.constants import LogEventSignature
from matic.json_types import IBaseClientConfig
from matic.pos.exit_util import ExitUtil
from matic.utils.base_token import BaseToken
from matic.utils.web3_side_chain_client import Web3SideChainClient


class BridgeClient:
    """Base class for POS bridge with reusable methods."""

    client: Web3SideChainClient
    exit_util: ExitUtil

    def __init__(self, config: IBaseClientConfig):
        self.client = Web3SideChainClient(config)

    def is_checkpointed(self, tx_hash: bytes) -> bool:
        """Check if transaction is checkpointed."""
        return self.exit_util.is_checkpointed(tx_hash)

    def is_deposited(self, deposit_tx_hash: bytes) -> bool:
        """Check if deposit has finished after exit (StateSynced happened)."""
        client = self.client

        token = BaseToken(
            address=client.abi_manager.get_config(
                'Matic.GenesisContracts.StateReceiver'
            ),
            is_parent=False,
            name='StateReceiver',
            bridge_type='genesis',
            client=client,
        )

        receipt = client.parent.get_transaction_receipt(deposit_tx_hash)
        last_state_id = token.process_read(token.contract.method('lastStateId'))

        event_signature = LogEventSignature.STATE_SYNCED_EVENT
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
