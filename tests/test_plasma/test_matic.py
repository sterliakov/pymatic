from __future__ import annotations

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger
from matic.plasma import ERC20, PlasmaClient
from matic.utils.abi_manager import ABIManager


@pytest.mark.read()
def test_client_address(erc_20_matic_child: ERC20, erc_20):
    assert erc_20_matic_child.name == 'MRC20'
    assert erc_20_matic_child.address == erc_20['matic_child']


@pytest.mark.read()
def test_get_balance_child(erc_20_matic_child: ERC20, from_: HexAddress):
    balance = erc_20_matic_child.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_balance_parent(erc_20_matic_parent: ERC20, from_: HexAddress):
    balance = erc_20_matic_parent.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_allowance_parent(erc_20_matic_parent: ERC20, from_: HexAddress):
    allowance = erc_20_matic_parent.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


@pytest.mark.read()
def test_is_checkpointed(plasma_client: PlasmaClient):
    tx_hash = bytes.fromhex(
        '4c7ff498b7a3bca131ae88a52832879ae53653a69227c17d70265230ac6269f1'
    )
    assert plasma_client.is_checkpointed(tx_hash) is True


@pytest.mark.read()
def test_is_deposited(plasma_client: PlasmaClient):
    tx_hash = bytes.fromhex(
        'ccbc00bea5c0773abddc2e220efab71b25b6b8d1efdfd5418025cf852ce30cf3'
    )
    assert plasma_client.is_deposited(tx_hash) is True


@pytest.mark.offline()
def test_child_transfer_matic_return_transaction(
    erc_20_matic_child: ERC20,
    to: HexAddress,
    from_: HexAddress,
    from_pk: HexStr,
):
    amount = 1
    result = erc_20_matic_child.transfer(
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
def test_withdraw_start_return_tx(erc_20, erc_20_matic_child: ERC20, from_pk: HexStr):
    # Same
    result = erc_20_matic_child.withdraw_start(
        10, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    assert result['to'].lower() == erc_20['matic_child'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_parent_return_tx(erc_20, erc_20_matic_parent: ERC20, from_pk: HexStr):
    # Same
    result = erc_20_matic_parent.approve(
        10,
        from_pk,
        {'return_transaction': True},
    ).transaction_config

    assert result['to'].lower() == erc_20['matic'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_deposit_return_tx(
    abi_manager: ABIManager,
    erc_20_matic_parent: ERC20,
    from_: HexAddress,
    from_pk: HexStr,
):
    # Diff
    result = erc_20_matic_parent.deposit(
        9, from_, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    root_chain_manager = abi_manager.get_config('Main.Contracts.DepositManagerProxy')
    assert result['to'].lower() == root_chain_manager.lower()


EXITED_TX_HASH = bytes.fromhex(
    '04495c5507293a9583e0e1249b0f2b981eebbe475b3e7b19bd754f72ea7d2a18'
)


# New
@pytest.mark.offline()
def test_withdraw_confirm_return_tx(
    erc_20_matic_parent: ERC20, from_pk: HexStr, abi_manager: ABIManager
):
    result = erc_20_matic_parent.withdraw_confirm(
        EXITED_TX_HASH, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    erc_20_predicate = abi_manager.get_config('Main.Contracts.ERC20Predicate')
    assert result['to'].lower() == erc_20_predicate.lower()


# New
@pytest.mark.offline()
def test_withdraw_confirm_faster_return_tx(
    erc_20_matic_parent: ERC20, from_pk: HexStr, abi_manager: ABIManager
):
    result = erc_20_matic_parent.withdraw_confirm_faster(
        EXITED_TX_HASH, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    erc_20_predicate = abi_manager.get_config('Main.Contracts.ERC20Predicate')

    assert result['to'].lower() == erc_20_predicate.lower()


@pytest.mark.offline()
def test_withdraw_exit_return_tx(
    abi_manager: ABIManager, erc_20_matic_parent: ERC20, from_pk: HexStr
):
    # Diff
    result = erc_20_matic_parent.withdraw_exit(
        from_pk,
        {'return_transaction': True, 'gas_limit': 200_000},
    ).transaction_config

    withdraw_manager = abi_manager.get_config('Main.Contracts.WithdrawManagerProxy')
    assert result['to'].lower() == withdraw_manager.lower()


@pytest.mark.online()
def test_child_transfer(
    erc_20,
    erc_20_matic_child: ERC20,
    plasma_client_for_to: PlasmaClient,
    to: HexAddress,
    from_: HexAddress,
    from_pk: HexStr,
    to_private_key: HexStr,
):
    # Same
    old_balance = erc_20_matic_child.get_balance(to)
    amount = 10
    result = erc_20_matic_child.transfer(amount, to, from_pk, {'gas_limit': 300_000})

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

    new_balance = erc_20_matic_child.get_balance(to)
    assert new_balance == old_balance + amount

    # transfer money back to user
    erc_20_child_token = plasma_client_for_to.erc_20(erc_20['child'])
    result = erc_20_child_token.transfer(
        amount, from_, to_private_key, {'gas_limit': 300_000}
    )
    logger.info('Back: %s', result.transaction_hash.hex())
    result.receipt
