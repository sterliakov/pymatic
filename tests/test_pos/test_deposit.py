import time

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger
from matic.pos import ERC20, ERC721, ERC1155, POSClient

from .test_erc_1155 import TOKEN_ID


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_deposit(
    pos_client: POSClient,
    erc_20_child: ERC20,
    erc_20_parent: ERC20,
    erc_721_child: ERC721,
    erc_721_parent: ERC721,
    erc_1155_child: ERC1155,
    erc_1155_parent: ERC1155,
    from_pk: HexStr,
    from_: HexAddress,
    subtests,
):
    tx_hashes = {}

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

    with subtests.test('Approve ERC20'):
        assert approve_20.receipt.status
    with subtests.test('Approve ERC721'):
        assert approve_721.receipt.status
    with subtests.test('Approve ERC1155'):
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

    deposited = {}
    with subtests.test('Deposit ERC20'):
        assert deposit_20.receipt.status
        deposited['20'] = False
    with subtests.test('Deposit ERC721'):
        assert deposit_721.receipt.status
        deposited['721'] = False
    with subtests.test('Deposit ERC1155'):
        assert deposit_1155.receipt.status
        deposited['1155'] = False

    # Wait for all checkpoint events

    def are_all_deposited():
        ok = True  # No direct return, so we check all.
        for key in deposited:
            if deposited[key]:
                continue
            elif pos_client.is_deposited(tx_hashes[key]):
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

    with subtests.test('Verify ERC20 balance'):
        assert balance_child_20 + 10 == erc_20_child.get_balance(from_)
        assert balance_parent_20 - 10 == erc_20_parent.get_balance(from_)

    with subtests.test('Verify ERC721 balance'):
        assert balance_child_721 + 1 == erc_721_child.get_tokens_count(from_)
        assert balance_parent_721 - 1 == erc_721_parent.get_tokens_count(from_)

    with subtests.test('Verify ERC1155 balance'):
        assert balance_child_1155 + 1 == erc_1155_child.get_balance(from_, TOKEN_ID)
        assert balance_parent_1155 - 1 == erc_1155_parent.get_balance(from_, TOKEN_ID)
