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

    # Approve
    approve_20 = erc_20_parent.approve(10, from_pk, {'gas_limit': 300_000})
    logger.info('Approve tx hash [ERC20]: %s', approve_20.transaction_hash.hex())

    assert approve_20.receipt.status
    logger.info('Allowance [ERC20]: %s', erc_20_parent.get_allowance(from_))

    # Deposit
    deposit_20 = erc_20_parent.deposit(10, from_, from_pk, {'gas_limit': 300_000})
    tx_hashes['20'] = deposit_20.transaction_hash
    logger.info('Deposit tx hash [ERC20]: %s', tx_hashes['20'].hex())

    token = erc_721_parent.get_all_tokens(from_, 1)[0]
    deposit_721 = erc_721_parent.safe_deposit(
        token, from_, from_pk, {'gas_limit': 300_000}
    )
    tx_hashes['721'] = deposit_721.transaction_hash
    logger.info('Deposit tx hash [ERC721]: %s', tx_hashes['721'].hex())

    # Finish both deposits
    assert deposit_20.receipt.status
    assert deposit_721.receipt.status

    # Wait for all checkpoint events
    deposited = {key: False for key in kinds}

    def are_all_deposited():
        ok = True  # No direct return, so we check all.
        for key in kinds:
            if deposited[key]:
                continue
            elif plasma_client.is_deposited(tx_hashes[key]):
                deposited[key] = True
                continue
            else:
                ok = False

        return ok

    start_time = time.time()
    timeout = 3 * 60 * 60
    while True:
        if are_all_deposited():
            break
        elif time.time() - start_time > timeout:
            pytest.fail(
                'Some transactions still not deposited: '
                + '\n'.join(
                    f'{kind}: {tx_hash.hex()}'
                    for kind, tx_hash in tx_hashes.items()
                    if not deposited[kind]
                )
            )
        else:
            time.sleep(30)

    assert balance_child_20 + 10 == erc_20_child.get_balance(from_)
    assert balance_child_721 + 1 == erc_721_child.get_tokens_count(from_)

    assert balance_parent_20 - 10 == erc_20_parent.get_balance(from_)
    assert balance_parent_721 - 1 == erc_721_parent.get_tokens_count(from_)
