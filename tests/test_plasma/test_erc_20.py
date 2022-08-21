from __future__ import annotations

import pytest

from matic import logger
from matic.exceptions import NullSpenderAddressException

WITHDRAW_EXITED_TX_HASH = bytes.fromhex(
    'd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
)


@pytest.mark.read()
def test_get_balance_child(erc_20_child, from_):
    # Same
    balance = erc_20_child.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_balance_parent(erc_20_parent, from_):
    # Same
    balance = erc_20_parent.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_allowance_child(erc_20_child, from_):
    # Same
    allowance = erc_20_child.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


@pytest.mark.read()
def test_get_allowance_parent(erc_20_parent, from_):
    # Same
    allowance = erc_20_parent.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


@pytest.mark.read()
def test_is_checkpointed(plasma_client):
    # Same
    assert plasma_client.is_checkpointed(WITHDRAW_EXITED_TX_HASH) is True


@pytest.mark.read()
def test_is_deposited(plasma_client):
    # Diff hashes
    tx_hash = '0xc3245a99dfbf2cf91d92ad535de9ee828208f0be3c0e101cba14d88e7849ed01'
    is_deposited = plasma_client.is_deposited(tx_hash)
    assert is_deposited is True


@pytest.mark.offline()
def test_child_transfer_return_transaction(erc_20_child, to, from_, from_pk, erc_20):
    # Same
    amount = 1
    result = erc_20_child.transfer(
        amount,
        to,
        from_pk,
        {'return_transaction': True},
    ).transaction_config
    assert result['chain_id'] == 80001
    assert result['to'] == erc_20['child']
    assert result['from'] == from_
    assert result['value'] == 0


# New
@pytest.mark.offline()
def test_child_transfer_matic_return_transaction(
    plasma_client, to, from_, from_pk, erc_20
):
    amount = 1
    matic_token = plasma_client.erc_20(None)
    result = matic_token.transfer(
        amount,
        to,
        from_pk,
        {'return_transaction': True},
    ).transaction_config
    assert 'data' not in result
    assert result['chain_id'] == 80001
    assert result['value'] == amount
    assert result['from'] == from_
    assert result['to'] == to


@pytest.mark.offline()
def test_parent_transfer_return_transaction_with_erp_1159(erc_20_parent, to, from_pk):
    # Same
    amount = 1
    result = erc_20_parent.transfer(
        amount,
        to,
        from_pk,
        {
            'max_fee_per_gas': 30,
            'max_priority_fee_per_gas': 30,
            'return_transaction': True,
        },
    ).transaction_config

    assert result['max_fee_per_gas'] == 30
    assert result['max_priority_fee_per_gas'] == 30
    assert 'gas_price' not in result
    assert result['chain_id'] == 5


@pytest.mark.offline()
def test_withdraw_start_return_tx(erc_20, erc_20_child, from_pk):
    # Same
    result = erc_20_child.withdraw_start(
        10, from_pk, {'return_transaction': True}
    ).transaction_config

    assert result['to'].lower() == erc_20['child'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_parent_return_tx(erc_20, erc_20_parent, from_pk):
    # Same
    result = erc_20_parent.approve(
        10,
        from_pk,
        {'return_transaction': True},
    ).transaction_config

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_parent_return_tx_with_spender_address(erc_20, erc_20_parent, from_pk):
    # Diff
    spender_address = erc_20_parent.predicate.address
    result = erc_20_parent.approve(
        1,
        from_pk,
        {'spender_address': spender_address, 'return_transaction': True},
    ).transaction_config

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_child_return_tx_without_spender_address(erc_20, erc_20_child, from_pk):
    # Same
    with pytest.raises(NullSpenderAddressException):
        erc_20_child.approve(1, from_pk)


@pytest.mark.offline()
def test_deposit_return_tx(abi_manager, erc_20_parent, from_, from_pk):
    # Diff
    result = erc_20_parent.deposit(
        9, from_, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    root_chain_manager = abi_manager.get_config('Main.Contracts.DepositManagerProxy')
    assert result['to'].lower() == root_chain_manager.lower()


EXITED_TX_HASH = bytes.fromhex(
    '95a6fd305456db15c431c5c4f082cf233cfeb0d4039bcf1d4cd713796fae0d2f'
)


# New
@pytest.mark.offline()
def test_withdraw_confirm_return_tx(erc_20_parent, from_pk, abi_manager):
    result = erc_20_parent.withdraw_confirm(
        EXITED_TX_HASH, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    erc_20_predicate = abi_manager.get_config('Main.Contracts.ERC20Predicate')
    assert result['to'].lower() == erc_20_predicate.lower()


# New
@pytest.mark.offline()
def test_withdraw_confirm_faster_return_tx(erc_20_parent, from_pk, abi_manager):
    result = erc_20_parent.withdraw_confirm_faster(
        EXITED_TX_HASH, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    erc_20_predicate = abi_manager.get_config('Main.Contracts.ERC20Predicate')

    assert result['to'].lower() == erc_20_predicate.lower()


@pytest.mark.offline()
def test_withdraw_exit_return_tx(abi_manager, erc_20_parent, from_pk):
    # Diff
    result = erc_20_parent.withdraw_exit(
        from_pk,
        {'return_transaction': True, 'gas_limit': 200_000},
    ).transaction_config

    withdraw_manager = abi_manager.get_config('Main.Contracts.WithdrawManagerProxy')
    assert result['to'].lower() == withdraw_manager.lower()


@pytest.mark.online()
def test_child_transfer(
    erc_20, erc_20_child, plasma_client_for_to, to, from_, from_pk, to_private_key
):
    # Same
    old_balance = erc_20_child.get_balance(to)
    amount = 10
    result = erc_20_child.transfer(amount, to, from_pk, {'gas_limit': 300_000})

    tx_hash = result.transaction_hash
    logger.info('Forward: %s', tx_hash.hex())
    assert tx_hash

    tx_receipt = result.get_receipt(timeout=5 * 60)
    assert tx_receipt.transaction_hash == tx_hash
    assert tx_receipt.from_.lower() == from_.lower()
    assert tx_receipt.to.lower() == erc_20['child'].lower()
    assert tx_receipt.type == '0x2'
    assert tx_receipt.gas_used > 0
    assert tx_receipt.cumulative_gas_used > 0
    assert tx_receipt.block_hash
    assert tx_receipt.block_number
    assert tx_receipt.logs_bloom
    assert tx_receipt.status

    new_balance = erc_20_child.get_balance(to)

    assert new_balance == old_balance + amount
    # transfer money back to user
    erc_20_child_token = plasma_client_for_to.erc_20(erc_20['child'])
    result = erc_20_child_token.transfer(
        amount, from_, to_private_key, {'gas_limit': 300_000}
    )
    logger.info('Back: %s', result.transaction_hash.hex())
    result.receipt
