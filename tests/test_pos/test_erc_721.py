from __future__ import annotations

import pytest
from eth_typing import HexAddress, HexStr

from matic.pos import ERC721, POSClient
from matic.utils.abi_manager import ABIManager


@pytest.mark.read()
def test_get_tokens_counts_child(erc_721_child: ERC721, from_: HexAddress):
    tokens_count = erc_721_child.get_tokens_count(from_)
    assert tokens_count > 0


@pytest.mark.read()
def test_get_tokens_count_parent(erc_721_parent: ERC721, from_: HexAddress):
    tokens_count = erc_721_parent.get_tokens_count(from_)
    assert tokens_count > 0


@pytest.mark.read()
def test_get_all_tokens_child(erc_721_child: ERC721, from_: HexAddress):
    tokens_count = erc_721_child.get_tokens_count(from_)
    all_tokens = erc_721_child.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


@pytest.mark.read()
def test_get_all_tokens_parent(erc_721_parent: ERC721, from_: HexAddress):
    tokens_count = erc_721_parent.get_tokens_count(from_)
    all_tokens = erc_721_parent.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


@pytest.mark.read()
def test_is_withdraw_exited(erc_721_parent: ERC721):
    tx_hash = bytes.fromhex(
        '2697a930ae883dd28c40a263a6a3b4d41a027cab56836de987ed2c2896abcdeb'
    )
    assert erc_721_parent.is_withdraw_exited(tx_hash) is True


@pytest.mark.read()
def test_is_deposited_for_deposit_many(pos_client: POSClient):
    deposit_txhash = bytes.fromhex(
        '2ae0f5073e0c0f96f622268ef8bc61ecec7349ffc97c61412e4f5cc157cb418e'
    )
    assert pos_client.is_deposited(deposit_txhash) is True


@pytest.mark.offline()
def test_transfer_return_tx(
    erc_721_child: ERC721, from_: HexAddress, to: HexAddress, from_pk: HexStr, erc_721
):
    all_tokens_from = erc_721_child.get_all_tokens(from_, 1)
    target_token = all_tokens_from[0]

    result = erc_721_child.transfer(
        target_token, from_, to, from_pk, {'return_transaction': True}
    ).transaction_config
    assert result['to'].lower() == erc_721['child'].lower()


@pytest.mark.offline()
def test_approve_return_tx(
    erc_721_parent: ERC721, from_: HexAddress, erc_721, from_pk: HexStr
):
    all_tokens = erc_721_parent.get_all_tokens(from_, 1)
    result = erc_721_parent.approve(
        all_tokens[0], from_pk, {'return_transaction': True}
    ).transaction_config
    assert result['to'].lower() == erc_721['parent'].lower()


@pytest.mark.offline()
def test_approve_all_return_tx(erc_721_parent: ERC721, erc_721, from_pk: HexStr):
    result = erc_721_parent.approve_all(
        from_pk, {'return_transaction': True}
    ).transaction_config
    assert result['to'].lower() == erc_721['parent'].lower()


@pytest.mark.offline()
def test_deposit_return_tx(
    erc_721_parent: ERC721, from_: HexAddress, abi_manager: ABIManager, from_pk: HexStr
):
    all_tokens = erc_721_parent.get_all_tokens(from_, 1)
    tx = erc_721_parent.deposit(
        all_tokens[0],
        from_,
        from_pk,
        {'return_transaction': True, 'gas_limit': 300_000},
    ).transaction_config
    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert tx['to'].lower() == root_chain_manager.lower()


@pytest.mark.offline()
def test_deposit_many_return_tx(
    erc_721_parent: ERC721, from_: HexAddress, from_pk: HexStr, abi_manager: ABIManager
):
    all_tokens = erc_721_parent.get_all_tokens(from_)
    tx = erc_721_parent.deposit_many(
        all_tokens, from_, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config
    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert tx['to'].lower() == root_chain_manager.lower()


@pytest.mark.offline()
def test_withdraw_start_return_tx(
    erc_721_child: ERC721, erc_721, from_: HexAddress, from_pk: HexStr
):
    all_tokens = erc_721_child.get_all_tokens(from_, 1)
    result = erc_721_child.withdraw_start(
        all_tokens[0], from_pk, {'return_transaction': True}
    ).transaction_config
    assert result['to'].lower() == erc_721['child'].lower()


@pytest.mark.offline()
def test_withdraw_start_with_meta_data_return_tx(
    erc_721_child: ERC721, erc_721, from_: HexAddress, from_pk: HexStr
):
    all_tokens = erc_721_child.get_all_tokens(from_, 1)
    result = erc_721_child.withdraw_start_with_metadata(
        all_tokens[0], from_pk, {'return_transaction': True}
    ).transaction_config
    assert result['to'].lower() == erc_721['child'].lower()


@pytest.mark.online()
def test_transfer_write(
    erc_721_child: ERC721,
    from_: HexAddress,
    to: HexAddress,
    erc_721,
    pos_client_for_to: POSClient,
    from_pk: HexStr,
    to_private_key: HexStr,
):
    all_tokens_from = erc_721_child.get_all_tokens(from_)
    all_tokens_to = erc_721_child.get_all_tokens(to)

    target_token = all_tokens_from[0]
    result = erc_721_child.transfer(
        target_token, from_, to, from_pk, {'gas_limit': 300_000}
    )

    tx_hash = result.transaction_hash
    tx_receipt = result.receipt

    try:
        assert tx_receipt
        assert tx_receipt.transaction_hash == tx_hash
        assert tx_receipt.from_ == from_
        assert tx_receipt.to.lower() == erc_721['child'].lower()
        assert tx_receipt.type == '0x2'
        assert tx_receipt.gas_used > 0
        assert tx_receipt.cumulative_gas_used > 0
        assert tx_receipt.status

        new_all_tokens_from = erc_721_child.get_all_tokens(from_)
        assert len(new_all_tokens_from) == len(all_tokens_from) - 1

        new_all_tokens_to = erc_721_child.get_all_tokens(to)
        assert len(new_all_tokens_to) == len(all_tokens_to) + 1
    finally:
        # transfer token back to sender
        erc721_child_token = pos_client_for_to.erc_721(erc_721['child'])
        result = erc721_child_token.transfer(
            target_token, to, from_, to_private_key, {'gas_limit': 300_000}
        )
        tx_hash = result.transaction_hash
        tx_receipt = result.receipt

        assert tx_receipt
        assert tx_receipt.status

        new_from_count = erc_721_child.get_tokens_count(from_)
        new_to_count = erc_721_child.get_tokens_count(to)

        assert new_from_count == len(all_tokens_from)
        assert new_to_count == len(all_tokens_to)
