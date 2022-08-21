import time

import pytest

from matic import logger

from .test_erc_1155 import TOKEN_ID


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_deposit(
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
    kinds = ('20', '721')

    balance_child_20 = erc_20_child.get_balance(from_)
    balance_child_721 = erc_721_child.get_tokens_count(from_)
    balance_child_1155 = erc_1155_child.get_balance(from_, TOKEN_ID)

    balance_parent_20 = erc_20_parent.get_balance(from_)
    balance_parent_721 = erc_721_parent.get_tokens_count(from_)
    balance_parent_1155 = erc_1155_parent.get_balance(from_, TOKEN_ID)

    # Approve
    approve_20 = erc_20_parent.approve(10, from_pk, {'gas_limit': 300_000})
    logger.info('Approve tx hash [ERC20]: %s', approve_20.transaction_hash.hex())

    token_721 = erc_721_parent.get_all_tokens(from_, 1)[0]
    approve_721 = erc_721_parent.approve(token_721, from_pk, {'gas_limit': 200_000})
    logger.info('Approve tx hash [ERC721]: %s', approve_721.transaction_hash.hex())

    approve_1155 = erc_1155_parent.approve_all(from_pk)
    logger.info('Approve tx hash [ERC1155]: %s', approve_1155.transaction_hash.hex())

    assert approve_20.receipt.status
    assert approve_721.receipt.status
    assert approve_1155.receipt.status

    # Deposit
    deposit_20 = erc_20_parent.deposit(10, from_, from_pk, {'gas_limit': 300_000})
    tx_hashes['20'] = deposit_20.transaction_hash
    logger.info('Deposit tx hash [ERC20]: %s', tx_hashes['20'].hex())

    deposit_721 = erc_721_parent.deposit(
        token_721, from_, from_pk, {'gas_limit': 200_000}
    )
    tx_hashes['721'] = deposit_721.transaction_hash
    logger.info('Deposit tx hash [ERC721]: %s', tx_hashes['721'].hex())

    deposit_1155 = erc_1155_parent.deposit(
        amount=1,
        token_id=TOKEN_ID,
        user_address=from_,
        private_key=from_pk,
        option={'gas_limit': 200_000},
    )
    tx_hashes['1155'] = deposit_1155.transaction_hash
    logger.info('Deposit tx hash [ERC1155]: %s', tx_hashes['1155'].hex())

    assert deposit_20.receipt.status
    assert deposit_721.receipt.status
    assert deposit_1155.receipt.status

    # Wait for all checkpoint events
    deposited = {key: False for key in kinds}

    def are_all_deposited():
        ok = True  # No direct return, so we check all.
        for key in kinds:
            if deposited[key]:
                continue
            elif pos_client.is_deposited(tx_hashes[key]):
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
                    f'{kind}: {tx_hash}'
                    for kind, tx_hash in tx_hashes.items()
                    if not deposited[kind]
                )
            )
        else:
            time.sleep(30)

    assert balance_child_20 + 10 == erc_20_child.get_balance(from_)
    assert balance_child_721 + 1 == erc_721_child.get_tokens_count(from_)
    assert balance_child_1155 + 1 == erc_1155_child.get_balance(from_, TOKEN_ID)

    assert balance_parent_20 - 10 == erc_20_parent.get_balance(from_)
    assert balance_parent_721 - 1 == erc_721_parent.get_tokens_count(from_)
    assert balance_parent_1155 - 1 == erc_1155_parent.get_balance(from_, TOKEN_ID)
