import time

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger
from matic.plasma import ERC20, ERC721, PlasmaClient


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_withdraw_full_cycle(
    plasma_client: PlasmaClient,
    erc_20_child: ERC20,
    erc_20_parent: ERC20,
    erc_721_child: ERC721,
    erc_721_parent: ERC721,
    from_pk: HexStr,
    from_: HexAddress,
):
    tx_hashes = {}
    kinds = ('20', '721')

    balance_child_20 = erc_20_child.get_balance(from_)
    balance_child_721 = erc_721_child.get_tokens_count(from_)

    balance_parent_20 = erc_20_parent.get_balance(from_)
    balance_parent_721 = erc_721_parent.get_tokens_count(from_)

    # Start all transactions
    start_20 = erc_20_child.withdraw_start(10, from_pk, {'gas_limit': 300_000})
    tx_hashes['20'] = start_20.transaction_hash
    logger.info('Start hash [ERC20]: %s', tx_hashes['20'].hex())

    token = erc_721_child.get_all_tokens(from_, 1)[0]
    start_721 = erc_721_child.withdraw_start(
        token, from_pk, option={'gas_limit': 300_000}
    )
    tx_hashes['721'] = start_721.transaction_hash
    logger.info('Start hash [ERC721]: %s', tx_hashes['721'].hex())

    # Wait for them to be dispatched
    assert start_20.receipt.status
    assert start_721.receipt.status

    # Wait for all checkpoint events
    checkpointed = {key: False for key in kinds}

    def are_all_checkpointed():
        ok = True  # No direct return, so we check all.
        for key in kinds:
            if checkpointed[key]:
                continue
            elif plasma_client.is_checkpointed(tx_hashes[key]):
                checkpointed[key] = True
                continue
            else:
                ok = False

        return ok

    timeout, interval = 3 * 60 * 60, 60
    for elapsed in range(timeout // interval):
        logger.info('Elapsed time: %d minutes.', elapsed)
        if are_all_checkpointed():
            break
        else:
            time.sleep(interval)
    else:
        pytest.fail(
            'Some transactions still not checkpointed: '
            + '\n'.join(
                f'{kind}: {tx_hash.hex()}'
                for kind, tx_hash in tx_hashes.items()
                if not checkpointed[kind]
            )
        )

    confirm_20 = erc_20_parent.withdraw_confirm(tx_hashes['20'], from_pk)
    assert confirm_20.transaction_hash
    logger.info('End hash [ERC20]: %s', confirm_20.transaction_hash.hex())

    confirm_721 = erc_721_parent.withdraw_confirm_faster(tx_hashes['721'], from_pk)
    logger.info('End hash [ERC721]: %s', confirm_721.transaction_hash.hex())
    assert confirm_721.transaction_hash

    assert confirm_20.receipt.status
    assert confirm_721.receipt.status

    end_20 = erc_20_parent.withdraw_exit(from_pk)
    assert end_20.transaction_hash
    logger.info('End hash [ERC20]: %s', end_20.transaction_hash.hex())

    end_721 = erc_721_parent.withdraw_exit(from_pk)
    logger.info('End hash [ERC721]: %s', end_721.transaction_hash.hex())
    assert end_721.transaction_hash

    assert end_20.receipt.status
    assert end_721.receipt.status

    assert balance_child_20 - 10 == erc_20_child.get_balance(from_)
    assert balance_child_721 - 1 == erc_721_child.get_tokens_count(from_)

    assert balance_parent_20 + 10 == erc_20_parent.get_balance(from_)
    assert balance_parent_721 + 1 == erc_721_parent.get_tokens_count(from_)
