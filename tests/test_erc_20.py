from __future__ import annotations

import pytest

from matic.web3_client import setup

setup()

from matic import services  # noqa: E402
from matic.exceptions import (  # noqa: E402
    NullSpenderAddressException,
    ProofAPINotSetException,
)


@pytest.fixture()
def erc_20(pos):
    return {'parent': pos['parent']['erc_20'], 'child': pos['child']['erc_20']}


@pytest.fixture()
def erc_20_child(pos_client, erc_20):
    return pos_client.erc_20(erc_20['child'])


@pytest.fixture()
def erc_20_parent(pos_client, erc_20):
    return pos_client.erc_20(erc_20['parent'], True)


def test_deposit_ether(pos_client, from_, from_pk):
    res = pos_client.deposit_ether(10, from_, from_pk, {})
    res.get_receipt(5 * 60)


def test_get_balance_child(erc_20_child, from_):
    balance = erc_20_child.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


def test_get_balance_parent(erc_20_parent, from_):
    balance = erc_20_parent.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


def test_get_allowance_child(erc_20_child, from_):
    allowance = erc_20_child.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


def test_get_allowance_parent(erc_20_parent, from_):
    allowance = erc_20_parent.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


def test_is_checkpointed(pos_client):
    assert (
        pos_client.is_checkpointed(
            bytes.fromhex(
                'd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
            )
        )
        is True
    )


def test_is_withdraw_exited(erc_20_parent):
    # exit_tx_hash = (
    #     '0x95844235073da694e311dc90476c861e187c36f86a863a950534c9ac2b7c1a48'
    # )
    is_exited = erc_20_parent.is_withdraw_exited(
        bytes.fromhex(
            'd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
        )
    )
    assert is_exited is True


def test_child_transfer_return_transaction_with_erp_1159(erc_20_child, to, from_pk):
    amount = 100
    # with pytest.raises(EIP1559NotSupportedException):
    erc_20_child.transfer(
        amount,
        to,
        from_pk,
        {
            'max_fee_per_gas': 10,
            'max_priority_fee_per_gas': 10,
            'return_transaction': True,
        },
    )


def test_child_transfer_return_transaction(erc_20_child, to, from_pk):
    amount = 1
    result = erc_20_child.transfer(
        amount,
        to,
        from_pk,
        {'return_transaction': True},
    )
    assert 'max_fee_per_gas' not in result
    assert 'max_priority_fee_per_gas' not in result
    # was commented out
    # assert result['gas_price'] > 0
    assert result['chain_id'] == 80001


def test_parent_transfer_return_transaction_with_erp_1159(erc_20_parent, to, from_pk):
    amount = 1
    result = erc_20_parent.transfer(
        amount,
        to,
        from_pk,
        {
            'max_fee_per_gas': 20,
            'max_priority_fee_per_gas': 20,
            'return_transaction': True,
        },
    )

    assert result['max_fee_per_gas'] == 20
    assert result['max_priority_fee_per_gas'] == 20
    assert 'gas_price' not in result
    assert result['chain_id'] == 5


def test_is_deposited(pos_client):
    tx_hash = '0xc67599f5c967f2040786d5924ec55d37bf943c009bdd23f3b50e5ae66efde258'
    is_deposited = pos_client.is_deposited(tx_hash)
    assert is_deposited is True


def test_withdraw_start_return_tx(erc_20, erc_20_child, from_pk):
    result = erc_20_child.withdraw_start(10, from_pk, {'return_transaction': True})

    assert result['to'].lower() == erc_20['child'].lower()
    assert 'data' in result


def test_approve_parent_return_tx(erc_20, erc_20_parent, from_pk):
    result = erc_20_parent.approve(
        10,
        from_pk,
        {'return_transaction': True},
    )

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


def test_approve_parent_return_tx_with_spender_address(erc_20, erc_20_parent, from_pk):
    spender_address = erc_20_parent.predicate_address
    result = erc_20_parent.approve(
        1,
        from_pk,
        {'spender_address': spender_address, 'return_transaction': True},
    )

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


def test_approve_child_return_tx_without_spender_address(erc_20, erc_20_child, from_pk):
    with pytest.raises(NullSpenderAddressException):
        erc_20_child.approve(1, from_pk)


def test_deposit_return_tx(abi_manager, erc_20_parent, from_, from_pk):
    result = erc_20_parent.deposit(
        9, from_, from_pk, {'return_transaction': True, 'gas_limit': 200000}
    )

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


exit_data = bytes.fromhex(
    '3805550f00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000741f9073e8423d1ec00b90100607e346e173cb8dcb5786265cc1264562462e3d0d4a14122bc088c6e35c23167a1c79f16dc17a2aaab85e5f759e18a40db750f262155e489c5f9b8dfa759ef1cea7fbf33ba48e44e44e2e2b5ca8a61bb32bcb7f14f7eb7e853f6698681a0356d564de85c8772fbd0b15dce8168ef9965d53cef0947d80fe8e3d562c5fccdffa89bf8ddfc998afe2723c5f99b9cca0c960953809513203979e077808d59620556fd0bb97fc4896508954b02c19b90fd244a391e50fe0cd6b979ff1afa1ac2a2e6432bcb168e3932a52c0d460fb2e93a4fc730e5bd0ccc9e42c2755a04a0800bc70068067197f28641cdbdf52915e48cc4eb65a6a74b37694bbee0ad96ce46751984013f8974846180c3c8a01c231c504b86cd2bbf2360e61bf747207ee2fbfc6f35005c328005c600e9255ca0ea31d8804cd84c283be9702b4de7eff615884681cc7c4cfdc65a46673eeb566cb902eaf902e701828547b9010000000000400000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000001800000000000000000080000010000000000000000000010000000000000000000000040000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000000020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a00000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000011f9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000007c1fcb8018000000000000000000000000000000000000000000000000056bc077dda68980000000000000000000000000000000000000000000000001ded4a9e3b2e378e3ca0000000000000000000000000000000000000000000000056bbffbbddb0968000000000000000000000000000000000000000000000001ded4aa5fd2aef8fbcab902f6f902f3f902f0822080b902eaf902e701828547b9010000000000400000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000001800000000000000000080000010000000000000000000010000000000000000000000040000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000000020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a00000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000011f9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000007c1fcb8018000000000000000000000000000000000000000000000000056bc077dda68980000000000000000000000000000000000000000000000001ded4a9e3b2e378e3ca0000000000000000000000000000000000000000000000056bbffbbddb0968000000000000000000000000000000000000000000000001ded4aa5fd2aef8fbca8200808000000000000000000000000000000000000000000000000000000000000000'
)

EXITED_TX_HASH = bytes.fromhex(
    'b005d8db45f33836c422ee18286fa8ebe49b4ec7b9930e673d85ecd081cc3b8e'
)


def test_withdraw_exit_return_tx(abi_manager, erc_20_parent):
    result = erc_20_parent.withdraw_exit(
        EXITED_TX_HASH,
        {'return_transaction': True, 'gas_limit': 200000},
    )
    assert result['data'].hex() == exit_data.hex()

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


def test_withdraw_exit_faster_return_tx_without_set_proof_api(erc_20_parent):
    with pytest.raises(ProofAPINotSetException):
        erc_20_parent.withdraw_exit_faster(EXITED_TX_HASH, {'return_transaction': True})


def test_call_get_block_included():
    services.DEFAULT_PROOF_API_URL = 'https://apis.matic.network/api/v1/'

    result = services.get_block_included('testnet', 1000)
    int(result['start'])
    assert result['start']  # may be '0'
    assert int(result['end'])
    assert result['headerBlockNumber'].startswith('0x')
    assert result['proposer'].startswith('0x')
    assert result['root'].startswith('0x')
    assert int(result['blockNumber']) == 1000
    assert int(result['createdAt'])


def test_withdraw_exit_faster_return_tx(abi_manager, erc_20_parent):
    services.DEFAULT_PROOF_API_URL = 'https://apis.matic.network/api/v1'

    result = erc_20_parent.withdraw_exit_faster(
        EXITED_TX_HASH, {'return_transaction': True, 'gas_limit': 200000}
    )
    assert result['data'] == exit_data

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


def test_child_transfer(
    erc_20, erc_20_child, pos_client_for_to, to, from_, from_pk, to_private_key
):
    old_balance = erc_20_child.get_balance(to)
    amount = 10
    result = erc_20_child.transfer(amount, to, from_pk)

    tx_hash = result.transaction_hash
    erc_20_child.client.logger.info('Forward: %s', tx_hash.hex())
    print('Forward: ', tx_hash.hex())
    assert tx_hash

    tx_receipt = result.get_receipt(timeout=5 * 60)
    assert tx_receipt.transaction_hash == tx_hash
    # assert(tx_receipt).to.be.an('object')
    assert tx_receipt.from_.lower() == from_.lower()
    assert tx_receipt.to.lower() == erc_20['child'].lower()
    assert tx_receipt.type == '0x2'
    assert tx_receipt.gas_used > 0
    assert tx_receipt.cumulative_gas_used > 0

    # was about hasattr, but it is weird for dataclasses
    assert tx_receipt.block_hash
    assert tx_receipt.block_number
    # assert tx_receipt.events  # no events in fact
    assert tx_receipt.logs_bloom
    assert tx_receipt.status
    assert tx_receipt.transaction_index
    # assert tx_receipt.logs

    new_balance = erc_20_child.get_balance(to)

    assert new_balance == old_balance + amount
    # transfer money back to user
    erc_20_child_token = pos_client_for_to.erc_20(erc_20['child'])
    result = erc_20_child_token.transfer(amount, from_, to_private_key)
    print('Back: ', result.transaction_hash.hex())
    result.receipt


def test_approve_and_deposit(erc_20_parent, from_, from_pk):
    result = erc_20_parent.approve(10, from_pk)
    assert result.transaction_hash
    print(result.transaction_hash)

    tx_receipt = result.receipt
    assert tx_receipt.type == '0x2'

    result = erc_20_parent.deposit(10, from_, from_pk)

    assert result.transaction_hash
    print(result.transaction_hash)

    result.receipt


@pytest.mark.can_timeout
@pytest.mark.trylast
def test_withdraw_full_cycle(pos_client, erc_20_child, erc_20_parent, from_pk):
    import time

    start = erc_20_child.withdraw_start(10, from_pk)
    tx_hash = start.transaction_hash
    print(tx_hash.hex())
    assert start.receipt

    start_time = time.time()
    timeout = 20 * 60
    while True:
        if pos_client.is_checkpointed(tx_hash):
            break
        elif time.time() - start_time > timeout:
            pytest.fail(f'Transaction {tx_hash.hex()} still not checkpointed')
        else:
            time.sleep(10)

    end = erc_20_parent.withdraw_exit(tx_hash)
    print(end.transaction_hash.hex())
    assert end.transaction_hash
    assert end.receipt
