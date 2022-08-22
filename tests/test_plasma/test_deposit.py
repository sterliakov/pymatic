import time

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger
from matic.plasma import ERC20, ERC721, PlasmaClient


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_deposit(
    plasma_client: PlasmaClient,
    erc_20_child: ERC20,
    erc_20_parent: ERC20,
    erc_20_matic_child: ERC20,
    erc_20_matic_parent: ERC20,
    erc_721_child: ERC721,
    erc_721_parent: ERC721,
    from_pk: HexStr,
    from_: HexAddress,
    subtests,
):
    tx_hashes = {}

    balance_child_20 = erc_20_child.get_balance(from_)
    # balance_child_matic_20 = erc_20_matic_child.get_balance(from_)
    balance_child_721 = erc_721_child.get_tokens_count(from_)

    balance_parent_20 = erc_20_parent.get_balance(from_)
    # balance_parent_matic_20 = erc_20_matic_parent.get_balance(from_)
    balance_parent_721 = erc_721_parent.get_tokens_count(from_)

    # Approve
    approve_20 = erc_20_parent.approve(10, from_pk, {'gas_limit': 300_000})
    logger.info('Approve tx hash [ERC20]: %s', approve_20.transaction_hash.hex())
    approve_20_matic = erc_20_matic_parent.approve(10, from_pk, {'gas_limit': 300_000})
    logger.info('Approve tx hash [MATIC]: %s', approve_20_matic.transaction_hash.hex())

    with subtests.test('Approve ERC20'):
        assert approve_20.receipt.status
        logger.info('Allowance [ERC20]: %s', erc_20_parent.get_allowance(from_))
    with subtests.test('Approve MATIC'):
        assert approve_20_matic.receipt.status
        logger.info('Allowance [MATIC]: %s', erc_20_matic_parent.get_allowance(from_))

    # Deposit
    deposit_20 = erc_20_parent.deposit(10, from_, from_pk, {'gas_limit': 300_000})
    tx_hashes['20'] = deposit_20.transaction_hash
    logger.info('Deposit tx hash [ERC20]: %s', tx_hashes['20'].hex())

    deposit_20_matic = erc_20_matic_parent.deposit(
        10, from_, from_pk, {'gas_limit': 300_000}
    )
    tx_hashes['MATIC'] = deposit_20_matic.transaction_hash
    logger.info('Deposit tx hash [MATIC]: %s', tx_hashes['MATIC'].hex())

    token = erc_721_parent.get_all_tokens(from_, 1)[0]
    deposit_721 = erc_721_parent.safe_deposit(
        token, from_, from_pk, {'gas_limit': 300_000}
    )
    tx_hashes['721'] = deposit_721.transaction_hash
    logger.info('Deposit tx hash [ERC721]: %s', tx_hashes['721'].hex())

    # Finish both deposits
    deposited = {}
    with subtests.test('Deposit ERC20'):
        assert deposit_20.receipt.status
        deposited['20'] = False
    with subtests.test('Deposit MATIC'):
        assert deposit_20_matic.receipt.status
        deposited['MATIC'] = False
    with subtests.test('Deposit ERC721'):
        assert deposit_721.receipt.status
        deposited['721'] = False

    # Wait for all checkpoint events

    def are_all_deposited():
        ok = True  # No direct return, so we check all.
        for key in deposited:
            if deposited[key]:
                continue
            elif plasma_client.is_deposited(tx_hashes[key]):
                deposited[key] = True
                continue
            else:
                ok = False

        return ok

    timeout, interval = 3 * 60 * 60, 60
    for elapsed in range(timeout // interval):
        logger.info('Elapsed time: %d minutes.', elapsed)
        if are_all_deposited():
            break
        else:
            time.sleep(interval)
    else:
        pytest.fail(
            'Some transactions still not deposited: '
            + '\n'.join(
                f'{kind}: {tx_hash.hex()}'
                for kind, tx_hash in tx_hashes.items()
                if not deposited[kind]
            )
        )

    with subtests.test('Confirm ERC20 balance'):
        assert balance_child_20 + 10 == erc_20_child.get_balance(from_)
        assert balance_parent_20 - 10 == erc_20_parent.get_balance(from_)

    with subtests.test('Confirm ERC721 balance'):
        assert balance_child_721 + 1 == erc_721_child.get_tokens_count(from_)
        assert balance_parent_721 - 1 == erc_721_parent.get_tokens_count(from_)
