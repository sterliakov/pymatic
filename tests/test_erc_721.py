from __future__ import annotations

import pytest

# import { erc721, from_, pos_client, pos_client_for_to, to, } from "./client"
# import { expect } from 'chai'
# import { ABIManager, setProofApi } from '@maticnetwork/maticjs'


@pytest.fixture()
def erc_721(pos):
    return {'parent': pos['parent']['erc_721'], 'child': pos['child']['erc_721']}


@pytest.fixture()
def erc_721_child(pos_client, erc_721):
    return pos_client.erc_721(erc_721['child'])


@pytest.fixture()
def erc_721_parent(pos_client, erc_721):
    return pos_client.erc_721(erc_721['parent'], True)


def test_get_tokens_counts_child(erc_721_child, from_):
    tokens_count = erc_721_child.get_tokens_count(from_)
    assert tokens_count >= 0


def test_get_tokens_count_parent(erc_721_parent, from_):
    tokens_count = erc_721_parent.get_tokens_count(from_)
    # console.log('tokens_count', tokens_count)
    assert tokens_count >= 0


def test_get_all_tokens_child(erc_721_child, from_):
    tokens_count = erc_721_child.get_tokens_count(from_)
    all_tokens = erc_721_child.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


def test_get_all_tokens_parent(erc_721_parent, from_):
    tokens_count = erc_721_parent.get_tokens_count(from_)
    all_tokens = erc_721_parent.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


def test_is_withdraw_exited(erc_721_parent):
    # exit_hash = '0xa3ed203336807249dea53dc99434e2d06b71c85f55c89ee49ca10244ab3dbcf5'
    is_exited = erc_721_parent.is_withdraw_exited(
        '0x2697a930ae883dd28c40a263a6a3b4d41a027cab56836de987ed2c2896abcdeb'
    )
    assert is_exited is True


def test_is_deposited_for_deposit_many(pos_client):
    deposit_txhash = (
        '0x2ae0f5073e0c0f96f622268ef8bc61ecec7349ffc97c61412e4f5cc157cb418e'
    )
    is_exited = pos_client.is_deposited(deposit_txhash)
    assert is_exited is True


def test_transfer_return_tx(erc_721_child, from_, to, from_pk, erc_721):
    all_tokens_from = erc_721_child.get_all_tokens(from_)
    target_token = all_tokens_from[0]

    result = erc_721_child.transfer(
        target_token, from_, to, from_pk, {'return_transaction': True}
    )
    # console.log(result)
    assert result['to'].lower() == erc_721['child'].lower()


def test_approve_return_tx(erc_721_parent, from_, erc_721, from_pk):
    all_tokens = erc_721_parent.get_all_tokens(from_)
    result = erc_721_parent.approve(
        all_tokens[0], from_pk, {'return_transaction': True}
    )
    assert result['to'].lower() == erc_721['parent'].lower()


def test_approve_all_return_tx(erc_721_parent, erc_721, from_pk):
    result = erc_721_parent.approve_all(from_pk, {'return_transaction': True})
    assert result['to'].lower() == erc_721['parent'].lower()


def test_deposit_return_tx(erc_721_parent, from_, abi_manager, from_pk):
    all_tokens = erc_721_parent.get_all_tokens(from_)
    tx = erc_721_parent.deposit(
        all_tokens[0],
        from_,
        from_pk,
        {'return_transaction': True, 'gas_limit': 300_000},
    )
    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert tx['to'].lower() == root_chain_manager.lower()


def test_deposit_many_return_tx(erc_721_parent, from_, from_pk, abi_manager):
    all_tokens = erc_721_parent.get_all_tokens(from_)
    tx = erc_721_parent.deposit_many(
        all_tokens, from_, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    )
    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert tx['to'].lower() == root_chain_manager.lower()


def test_withdraw_start_return_tx(erc_721_child, erc_721, from_, from_pk):
    all_tokens = erc_721_child.get_all_tokens(from_)
    result = erc_721_child.withdraw_start(
        all_tokens[0], from_pk, {'return_transaction': True}
    )
    assert result['to'].lower() == erc_721['child'].lower()


def test_withdraw_start_with_meta_data_return_tx(
    erc_721_child, erc_721, from_, from_pk
):
    all_tokens = erc_721_child.get_all_tokens(from_)
    result = erc_721_child.withdraw_start_with_metadata(
        all_tokens[0], from_pk, {'return_transaction': True}
    )
    assert result['to'].lower() == erc_721['child'].lower()


def test_transfer_write(
    erc_721_child, from_, to, erc_721, pos_client_for_to, from_pk, to_private_key
):
    all_tokens_from = erc_721_child.get_all_tokens(from_)
    # // console.log('all_tokens_from', all_tokens_from)
    all_tokens_to = erc_721_child.get_all_tokens(to)
    # // console.log('all_tokens_to', all_tokens_to)

    target_token = all_tokens_from[0]
    result = erc_721_child.transfer(
        target_token, from_, to, from_pk, {'gas_limit': 300_000}
    )

    tx_hash = result.transaction_hash
    tx_receipt = result.get_receipt()

    try:
        assert tx_receipt.transaction_hash == tx_hash
        # assert tx_receipt).to.be.an('object')
        assert tx_receipt.from_ == from_
        assert tx_receipt.to.lower() == erc_721['child'].lower()
        assert tx_receipt.type == '0x2'
        assert tx_receipt.gas_used > 0
        assert tx_receipt.cumulative_gas_used > 0

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

        new_from_count = erc_721_child.get_tokens_count(from_)
        new_to_count = erc_721_child.get_tokens_count(to)

        assert new_from_count == len(all_tokens_from)
        assert new_to_count == len(all_tokens_to)


# if (process.env.NODE_ENV !== 'test_all') return


def test_approve(erc_721, erc_721_parent, from_, from_pk):
    all_tokens = erc_721_parent.get_all_tokens(from_)
    result = erc_721_parent.approve(
        all_tokens[0], from_pk, {'return_transaction': True}
    )
    assert result['to'].lower() == erc_721['parent'].lower()