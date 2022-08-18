from __future__ import annotations

import pytest

from matic import services

services.DEFAULT_PROOF_API_URL = 'https://apis.matic.network/api/v1/'


@pytest.fixture()
def erc_1155(pos):
    return {'parent': pos['parent']['erc_1155'], 'child': pos['child']['erc_1155']}


@pytest.fixture()
def erc_1155_child(pos_client, erc_1155):
    return pos_client.erc_1155(erc_1155['child'])


@pytest.fixture()
def erc_1155_parent(pos_client, erc_1155):
    return pos_client.erc_1155(erc_1155['parent'], True)


@pytest.mark.read()
def test_get_balance_child(erc_1155_child, from_):
    balance = erc_1155_child.get_balance(from_, 123)
    assert balance > 0


@pytest.mark.read()
def test_get_balance_parent(erc_1155_parent, from_):
    balance = erc_1155_parent.get_balance(from_, 123)
    assert balance > 0


@pytest.mark.read()
def test_is_withdraw_exited(erc_1155_parent):
    is_exited = erc_1155_parent.is_withdraw_exited(
        '0xbc48c0ccd9821141779a200586ef52033a3487c4e1419625fe7a0ea984521052'
    )
    assert is_exited is True


@pytest.mark.read()
def test_is_deposited(pos_client):
    tx_hash = '0x507ea7267693d477917265f52c23c08f1830215a0c7d86643b9c1fb4997a021e'
    is_deposited = pos_client.is_deposited(tx_hash)
    assert is_deposited is True


@pytest.mark.offline()
def test_transfer_return_tx(erc_1155_child, from_, to, from_pk, erc_1155):
    result = erc_1155_child.transfer(
        {'amount': 1, 'from_': from_, 'to': to, 'token_id': 123},
        from_pk,
        {'return_transaction': True, 'gas_limit': 200_000},
    )
    assert result['to'].lower() == erc_1155['child'].lower()


@pytest.mark.offline()
def test_approve_all_return_tx(erc_1155_parent, from_pk, erc_1155):
    result = erc_1155_parent.approve_all(from_pk, {'return_transaction': True})
    assert result['to'].lower() == erc_1155['parent'].lower()


@pytest.mark.offline()
def test_deposit_return_tx(abi_manager, erc_1155_parent, from_, from_pk):
    tx = erc_1155_parent.deposit(
        {'amount': 10, 'token_id': 123, 'user_address': from_},
        from_pk,
        {'return_transaction': True, 'gas_limit': 200_000},
    )
    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert tx['to'].lower() == root_chain_manager.lower()


# def test_deposit_many_return_tx(erc_1155_parent, abi_manager, from_):
#     tx = erc_1155_parent.deposit_many(all_tokens, from_, {
#         'return_transaction': True
#     })
#     root_chain_manager = abi_manager.get_config(
#         "Main.POSContracts.RootChainManagerProxy"
#     )
#     assert tx['to'].lower() == root_chain_manager.lower()


@pytest.mark.offline()
def test_withdraw_start_return_tx(erc_1155_child, erc_1155, from_pk):
    result = erc_1155_child.withdraw_start(
        123, 10, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    )
    assert result['to'].lower() == erc_1155['child'].lower()


@pytest.mark.offline()
def test_withdraw_start_many_return_tx(erc_1155_child, erc_1155, from_pk):
    result = erc_1155_child.withdraw_start_many(
        [123], [10], from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    )
    assert result['to'].lower() == erc_1155['child'].lower()


@pytest.mark.online()
def test_transfer_write(
    erc_1155_child, pos_client_for_to, to, from_, from_pk, to_private_key, erc_1155
):
    target_token = 123
    all_tokens_from = erc_1155_child.get_balance(from_, target_token)
    all_tokens_to = erc_1155_child.get_balance(to, target_token)
    amount_to_transfer = 1
    result = erc_1155_child.transfer(
        {
            'token_id': target_token,
            'from_': from_,
            'to': to,
            'amount': amount_to_transfer,
        },
        from_pk,
    )

    tx_hash = result.transaction_hash
    assert tx_hash
    tx_receipt = result.receipt

    assert tx_receipt.transaction_hash == tx_hash
    assert tx_receipt.from_ == from_
    assert tx_receipt.to.lower() == erc_1155['child'].lower()
    assert tx_receipt.type == '0x2'
    assert tx_receipt.gas_used > 0
    assert tx_receipt.cumulative_gas_used > 0

    new_all_tokens_from = erc_1155_child.get_balance(from_, target_token)
    assert new_all_tokens_from == all_tokens_from - 1
    new_all_tokens_to = erc_1155_child.get_balance(to, target_token)
    assert new_all_tokens_to == all_tokens_to + 1

    erc_1155_child_token = pos_client_for_to.erc_1155(erc_1155['child'])

    # transfer token back to sender
    result = erc_1155_child_token.transfer(
        {
            'token_id': target_token,
            'to': from_,
            'from_': to,
            'amount': amount_to_transfer,
        },
        to_private_key,
    )
    tx_hash = result.transaction_hash
    tx_receipt = result.receipt

    new_from_count = erc_1155_child.get_balance(from_, target_token)
    new_to_count = erc_1155_child.get_balance(to, target_token)

    assert new_from_count == all_tokens_from
    assert new_to_count == all_tokens_to


@pytest.mark.online()
def test_approve_and_deposit(erc_1155_parent, from_, from_pk):
    target_token = 123
    # all_tokens_from = erc_1155_child.get_balance(from_, target_token)

    approve_tx = erc_1155_parent.approve_all(from_pk)
    assert approve_tx.receipt

    deposit_tx = erc_1155_parent.deposit(
        {
            'amount': 1,
            'token_id': target_token,
            'user_address': from_,
        },
        from_pk,
    )
    assert deposit_tx.receipt


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_withdraw_full_cycle(pos_client, erc_1155_child, erc_1155_parent, from_pk):
    import time

    start = erc_1155_child.withdraw_start(123, 1, from_pk)
    tx_hash = start.transaction_hash
    erc_1155_child.client.logger.info('Start hash: %s', tx_hash.hex())
    assert start.receipt

    start_time = time.time()
    timeout = 3 * 60 * 60
    while True:
        if pos_client.is_checkpointed(tx_hash):
            break
        elif time.time() - start_time > timeout:
            pytest.fail(f'Transaction {tx_hash.hex()} still not checkpointed')
        else:
            time.sleep(10)

    end = erc_1155_parent.withdraw_exit(tx_hash, from_pk)
    erc_1155_child.client.logger.info('End hash: %s', end.transaction_hash.hex())
    assert end.transaction_hash
    assert end.receipt
