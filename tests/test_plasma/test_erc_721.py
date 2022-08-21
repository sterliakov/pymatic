from __future__ import annotations

import time

import pytest


@pytest.mark.read()
def test_get_tokens_counts_child(erc_721_child, from_):
    # Same
    tokens_count = erc_721_child.get_tokens_count(from_)
    assert tokens_count > 0


@pytest.mark.read()
def test_get_tokens_count_parent(erc_721_parent, from_):
    # Same
    tokens_count = erc_721_parent.get_tokens_count(from_)
    assert tokens_count > 0


@pytest.mark.read()
def test_get_all_tokens_child(erc_721_child, from_):
    # Same
    tokens_count = erc_721_child.get_tokens_count(from_)
    all_tokens = erc_721_child.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


@pytest.mark.read()
def test_get_all_tokens_parent(erc_721_parent, from_):
    # Same
    tokens_count = erc_721_parent.get_tokens_count(from_)
    all_tokens = erc_721_parent.get_all_tokens(from_)
    assert len(all_tokens) == tokens_count


@pytest.mark.read()
def test_is_deposited(plasma_client):
    # Diff
    deposit_txhash = bytes.fromhex(
        '041fd0e39d523b78aaeea92638f076b3d51fec5f587e0eebdfa2e0e11025c610'
    )
    assert plasma_client.is_deposited(deposit_txhash) is True


# New
@pytest.mark.offline()
def test_withdraw_exit_return_tx(erc_721_parent, abi_manager, from_pk):
    result = erc_721_parent.withdraw_exit(
        from_pk, {'return_transaction': True}
    ).transaction_config
    withdraw_manager = abi_manager.get_config('Main.Contracts.WithdrawManagerProxy')
    assert result['to'].lower() == withdraw_manager.lower()


@pytest.mark.online()
def test_safe_deposit(plasma_client, erc_721_child, erc_721_parent, from_, from_pk):
    child_balance = erc_721_child.get_tokens_count(from_)

    token = erc_721_parent.get_all_tokens(from_, 1)[0]

    deposit_tx = erc_721_parent.safe_deposit(
        token, from_, from_pk, {'gas_limit': 300_000}
    )
    receipt = deposit_tx.receipt
    assert receipt
    assert receipt.status
    tx_hash = deposit_tx.transaction_hash

    start_time = time.time()
    timeout = 60 * 60
    while True:
        if plasma_client.is_deposited(tx_hash):
            break
        elif time.time() - start_time > timeout:
            pytest.fail(f'Transaction {tx_hash.hex()} still not deposited')
        else:
            time.sleep(10)

    assert erc_721_child.get_tokens_count(from_) == child_balance + 1


@pytest.mark.online()
def test_transfer_write(
    erc_721_child, from_, to, erc_721, plasma_client_for_to, from_pk, to_private_key
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
        assert tx_receipt.status
        assert tx_receipt.transaction_hash == tx_hash
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
        erc721_child_token = plasma_client_for_to.erc_721(erc_721['child'])
        result = erc721_child_token.transfer(
            target_token, to, from_, to_private_key, {'gas_limit': 300_000}
        )
        tx_hash = result.transaction_hash
        tx_receipt = result.receipt

        new_from_count = erc_721_child.get_tokens_count(from_)
        new_to_count = erc_721_child.get_tokens_count(to)

        assert new_from_count == len(all_tokens_from)
        assert new_to_count == len(all_tokens_to)
