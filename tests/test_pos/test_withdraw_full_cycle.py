import time

import pytest

from matic import logger

from .test_erc_1155 import TOKEN_ID


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_withdraw_full_cycle(
    pos_client,
    erc_20_child,
    erc_20_parent,
    erc_721_child,
    erc_721_parent,
    erc_1155_child,
    erc_1155_parent,
    from_pk,
    from_,
):
    tx_hashes = {}
    kinds = ('20', '721', '1155')

    balance_child_20 = erc_20_child.get_balance(from_)
    balance_child_721 = erc_721_child.get_balance(from_)
    balance_child_1155 = erc_1155_child.get_balance(from_)

    balance_parent_20 = erc_20_parent.get_balance(from_)
    balance_parent_721 = erc_721_parent.get_balance(from_)
    balance_parent_1155 = erc_1155_parent.get_balance(from_)

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

    start_1155 = erc_1155_child.withdraw_start(
        TOKEN_ID, 1, from_pk, option={'gas_limit': 300_000}
    )
    tx_hashes['1155'] = start_1155.transaction_hash
    logger.info('Start hash [ERC1155]: %s', tx_hashes['1155'].hex())

    # Wait for them to be dispatched
    assert start_20.receipt.status
    assert start_721.receipt.status
    assert start_1155.receipt.status

    # Wait for all checkpoint events
    checkpointed = {key: False for key in kinds}

    def are_all_checkpointed():
        ok = True  # No direct return, so we check all.
        for key in kinds:
            if checkpointed[key]:
                continue
            elif pos_client.is_checkpointed(tx_hashes[key]):
                checkpointed[key] = True
                continue
            else:
                ok = False

        return ok

    start_time = time.time()
    timeout = 3 * 60 * 60
    while True:
        if are_all_checkpointed():
            break
        elif time.time() - start_time > timeout:
            pytest.fail(
                'Some transactions still not checkpointed: '
                + '\n'.join(
                    f'{kind}: {tx_hash}'
                    for kind, tx_hash in tx_hashes.items()
                    if not checkpointed[kind]
                )
            )
        else:
            time.sleep(30)

    end_20 = erc_20_parent.withdraw_exit(tx_hashes['20'], from_pk)
    assert end_20.transaction_hash
    logger.info('End hash [ERC20]: %s', end_20.transaction_hash.hex())

    end_721 = erc_721_parent.withdraw_exit(tx_hashes['721'], from_pk)
    logger.info('End hash [ERC721]: %s', end_721.transaction_hash.hex())
    assert end_721.transaction_hash

    end_1155 = erc_1155_parent.withdraw_exit(tx_hashes['1155'], from_pk)
    logger.info('End hash [ERC1155]: %s', end_1155.transaction_hash.hex())
    assert end_1155.transaction_hash

    assert end_20.receipt.status
    assert end_721.receipt.status
    assert end_1155.receipt.status

    assert balance_child_20 - 10 == erc_20_child.get_balance(from_)
    assert balance_child_721 - 1 == erc_721_child.get_balance(from_)
    assert balance_child_1155 - 1 == erc_1155_child.get_balance(from_)

    assert balance_parent_20 + 10 == erc_20_parent.get_balance(from_)
    assert balance_parent_721 + 1 == erc_721_parent.get_balance(from_)
    assert balance_parent_1155 + 1 == erc_1155_parent.get_balance(from_)
