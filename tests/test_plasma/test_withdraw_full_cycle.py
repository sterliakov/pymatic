import time

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger
from matic.plasma import ERC20, PlasmaClient

# def test_widthdraw_plasma_721(erc_721_parent, erc_721_child, from_, from_pk):
#     """Test is OK, but predicate was deployed with wrong WithdrawManager address.

#     See on etherscan:
#     https://goerli.etherscan.io/address/0x473cb675c9214f79dee10948443509c441a678e7#code

#     So all transactions with WithdrawManager for ERC721 fail.

#     I tried deploying separate contract with this fixed (just a copy via Remix),
#     and everything is OK until `checkPredicateAndTokenMapping` modifier check fires
#     on WithdrawManager (and this failure is 100% valid, since my contract is not
#     acknowledged as proper ERC721 predicate).
#     """
#     balance_child_721 = erc_721_child.get_tokens_count(from_)
#     balance_parent_721 = erc_721_parent.get_tokens_count(from_)

#     token = erc_721_child.get_all_tokens(from_, 1)[0]
#     start_721 = erc_721_child.withdraw_start(
#         token, from_pk, option={'gas_limit': 300_000}
#     )
#     tx_hash = start_721.transaction_hash
#     logger.info('Start hash [ERC721]: %s', tx_hash.hex())
#     assert start_721.receipt.status

#     confirm_721 = erc_721_parent.withdraw_confirm_faster(
#         tx_hash, from_pk, option={'gas_limit': 300_000}
#     )
#     assert confirm_721.transaction_hash
#     logger.info('Confirm hash [ERC721]: %s', confirm_721.transaction_hash.hex())
#     assert confirm_721.receipt.status

#     end_721 = erc_721_parent.withdraw_exit(from_pk)
#     assert end_721.transaction_hash
#     logger.info('End hash [ERC721]: %s', end_721.transaction_hash.hex())
#     assert end_721.receipt.status

#     assert balance_child_721 - 1 == erc_721_child.get_tokens_count(from_)
#     assert balance_parent_721 + 1 == erc_721_parent.get_tokens_count(from_)


@pytest.mark.can_timeout()
@pytest.mark.online()
@pytest.mark.trylast()
def test_withdraw_full_cycle(
    plasma_client: PlasmaClient,
    erc_20_child: ERC20,
    erc_20_parent: ERC20,
    erc_20_matic_child: ERC20,
    erc_20_matic_parent: ERC20,
    from_pk: HexStr,
    from_: HexAddress,
    subtests,
):
    tx_hashes = {}

    balance_child_20 = erc_20_child.get_balance(from_)
    balance_parent_20 = erc_20_parent.get_balance(from_)

    # Start all transactions

    # Wait for them to be dispatched
    checkpointed = {}
    with subtests.test('Begin ERC20'):
        start_20 = erc_20_child.withdraw_start(10, from_pk, {'gas_limit': 300_000})
        tx_hashes['20'] = start_20.transaction_hash
        logger.info('Start hash [ERC20]: %s', tx_hashes['20'].hex())
        assert start_20.receipt.status
        checkpointed['20'] = False

    with subtests.test('Begin MATIC'):
        start_20_matic = erc_20_matic_child.withdraw_start(
            10, from_pk, {'gas_limit': 300_000}
        )
        tx_hashes['MATIC'] = start_20_matic.transaction_hash
        logger.info('Start hash [MATIC]: %s', tx_hashes['MATIC'].hex())
        assert start_20_matic.receipt.status
        checkpointed['MATIC'] = False

    # Wait for all checkpoint events

    def are_all_checkpointed():
        ok = True  # No direct return, so we check all.
        for key in checkpointed:
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

    with subtests.test('Confirm ERC20'):
        confirm_20 = erc_20_parent.withdraw_confirm(tx_hashes['20'], from_pk)
        assert confirm_20.transaction_hash
        logger.info('Confirm hash [ERC20]: %s', confirm_20.transaction_hash.hex())
        assert confirm_20.receipt.status

    with subtests.test('Confirm MATIC'):
        confirm_20_matic = erc_20_matic_parent.withdraw_confirm(
            tx_hashes['MATIC'], from_pk
        )
        assert confirm_20_matic.transaction_hash
        logger.info('Confirm hash [MATIC]: %s', confirm_20_matic.transaction_hash.hex())
        assert confirm_20_matic.receipt.status

    with subtests.test('Finish ERC20'):
        end_20 = erc_20_parent.withdraw_exit(from_pk)
        assert end_20.transaction_hash
        logger.info('End hash [ERC20]: %s', end_20.transaction_hash.hex())
        assert end_20.receipt.status

    with subtests.test('Finish MATIC'):
        end_20_matic = erc_20_matic_parent.withdraw_exit(from_pk)
        assert end_20_matic.transaction_hash
        logger.info('End hash [MATIC]: %s', end_20_matic.transaction_hash.hex())
        assert end_20_matic.receipt.status

    with subtests.test('Verify ERC20 balance'):
        assert balance_child_20 - 10 == erc_20_child.get_balance(from_)
        assert balance_parent_20 + 10 == erc_20_parent.get_balance(from_)
