from __future__ import annotations

import os

import pytest
from web3 import Web3

from matic.web3_client import setup

setup()

from matic import services  # noqa: E402
from matic.exceptions import (  # noqa: E402
    NullSpenderAddressException,
    ProofAPINotSetException,
)
from matic.json_types import (  # noqa: E402
    ConfigWithFrom,
    IPOSClientConfig,
    NeighbourClientConfig,
)
from matic.pos import POSClient  # noqa: E402
from matic.utils.abi_manager import ABIManager  # noqa: E402

# import {
#     ABIManager, setProofApi, service, utils, ITransactionRequestConfig
# } from '@maticnetwork/maticjs'


# client.ts
@pytest.fixture()
def private_key(user1):
    return user1['private_key']


@pytest.fixture()
def from_(user1):
    return user1['address']


@pytest.fixture()
def to(user2):
    return user2['address']


@pytest.fixture()
def to_private_key(user2):
    return user2['private_key']


@pytest.fixture()
def child_provider(rpc):
    return Web3.HTTPProvider(rpc['child'])


@pytest.fixture()
def parent_provider(rpc):
    return Web3.HTTPProvider(rpc['parent'])


@pytest.fixture()
def erc_20(pos):
    return {'parent': pos['parent']['erc_20'], 'child': pos['child']['erc_20']}


# @pytest.fixture()
# def erc_721(pos):
#     return {'parent': pos['parent']['erc_721'], 'child': pos['child']['erc_721']}


# @pytest.fixture()
# def erc_1155(pos):
#     return {'parent': pos['parent']['erc_1155'], 'child': pos['child']['erc_1155']}


@pytest.fixture()
def pos_client(user1, parent_provider, child_provider):
    return POSClient(
        IPOSClientConfig(
            # log: true,
            network='testnet',
            version='mumbai',
            parent=NeighbourClientConfig(
                provider=parent_provider,
                default_config=ConfigWithFrom(user1['address']),
            ),
            child=NeighbourClientConfig(
                provider=child_provider,
                default_config=ConfigWithFrom(user1['address']),
            ),
        )
    )


@pytest.fixture()
def pos_client_for_to(user2, parent_provider, child_provider):
    return POSClient(
        IPOSClientConfig(
            # log: true,
            network='testnet',
            version='mumbai',
            parent=NeighbourClientConfig(
                provider=parent_provider,
                default_config=ConfigWithFrom(user2['address']),
            ),
            child=NeighbourClientConfig(
                provider=child_provider,
                default_config=ConfigWithFrom(user2['address']),
            ),
        )
    )


# end of client.ts


@pytest.fixture()
def erc_20_child(pos_client, erc_20):
    return pos_client.erc_20(erc_20['child'])


@pytest.fixture()
def erc_20_parent(pos_client, erc_20):
    return pos_client.erc_20(erc_20['parent'], True)


@pytest.fixture()
def abi_manager():
    return ABIManager('testnet', 'mumbai')


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
            '0xd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
        )
        is True
    )


def test_is_withdraw_exited(erc_20_parent):
    # exit_tx_hash = (
    #     '0x95844235073da694e311dc90476c861e187c36f86a863a950534c9ac2b7c1a48'
    # )
    is_exited = erc_20_parent.is_withdraw_exited(
        '0xd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
    )
    assert is_exited is True


def test_child_transfer_return_transaction_with_erp_1159(erc_20_child, to):
    amount = 100
    # with pytest.raises(EIP1559NotSupportedException):
    erc_20_child.transfer(
        amount,
        to,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {
            'max_fee_per_gas': 10,
            'max_priority_fee_per_gas': 10,
            'return_transaction': True,
        },
    )


def test_child_transfer_return_transaction(erc_20_child, to):
    amount = 1
    result = erc_20_child.transfer(
        amount,
        to,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'return_transaction': True},
    )
    assert 'max_fee_per_gas' not in result
    assert 'max_priority_fee_per_gas' not in result
    # was commented out
    # assert result['gas_price'] > 0
    assert result['chain_id'] == 80001


def test_parent_transfer_return_transaction_with_erp_1159(erc_20_parent, to):
    amount = 1
    result = erc_20_parent.transfer(
        amount,
        to,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
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


def test_withdrawstart_return_tx(erc_20, erc_20_child):
    result = erc_20_child.withdraw_start(
        10,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'return_transaction': True},
    )

    assert result['to'].lower() == erc_20['child'].lower()
    assert 'data' in result


def test_approve_parent_return_tx(erc_20, erc_20_parent):
    result = erc_20_parent.approve(
        10,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'return_transaction': True},
    )

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


def test_approve_parent_return_tx_with_spender_address(erc_20, erc_20_parent):
    spender_address = erc_20_parent.predicate_address
    result = erc_20_parent.approve(
        1,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'spender_address': spender_address, 'return_transaction': True},
    )

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


def test_approve_child_return_tx_without_spender_address(erc_20, erc_20_child):
    with pytest.raises(NullSpenderAddressException):
        erc_20_child.approve(
            1, '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36'
        )


def test_deposit_return_tx(abi_manager, erc_20_parent, from_):
    # spender_address = erc_20_parent.predicate_address
    print(erc_20_parent.get_balance(from_))
    print(erc_20_parent.get_allowance(from_))
    print(erc_20_parent.get_allowance(erc_20_parent.predicate_address))
    erc_20_parent.approve(
        10,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        # {'from': from_},
    )
    print(erc_20_parent.get_allowance(erc_20_parent.predicate_address))
    result = erc_20_parent.deposit(10, from_, {'return_transaction': True})

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


exit_data = bytes.fromhex(
    '3805550f00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000827f9082484235e69b0b9010031f7f7ef8848837caca0654cdd16c2c1af23e138d5ea431107325c6d99dfa567b8e395866f4fd177d79de4a8fec9d06ecea4223f55d1724e6c8455dc62148394266f9e732545254f25407139bd8cb3ecfbd9053933f23e1fca181659680cf4c1a5a6c6f723df2d7d35f3fc14929c8ccef3a9fff644db162a845ecf3a89f41b98436f15fada0f112ebea28f29e9e97f3635bd68ff97de3c0f5cdbd867bd8cb13af5930f55ca3b9ee8f345c3923965d2935a72bb4ddff77b6d5a8f427fbe79945d58189e2f58bec6c09e38c058bb80978eee60bcc260c883be329eb37a9c029e7d5733a173b53aeb0e92f925db4dc681d4bfa2f05c8c5fdd296230d1411b05264a84013c786a84617a6c24a0a317bf456e88f02bccaab4c7aa1a919485ee451901772eeff615a2ab305f3ca0a0984131328f0f9b4ffba09638e99ce4ec98b1aec6eb46eb3023078a03be9d51f8b902ebf902e801830743f9b9010000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000000800000000000000000080000010000000000000000000010000000008000000000000000000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000400020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000fd71dc9721d9ddcf0480a582927c3dcd42f3064ca00000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000af9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000fd71dc9721d9ddcf0480a582927c3dcd42f3064ca0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000005d17d8a0120000000000000000000000000000000000000000000000006f680513d061bb0d020000000000000000000000000000000000000000000001c57a98b6c5d67d41f500000000000000000000000000000000000000000000006f6804b6b8891afb020000000000000000000000000000000000000000000001c57a9913ddaf1d53f5b903dbf903d8f851a051de183267eca4127869bd2deab74a212d98ec445ea022f108006a65d32011b780808080808080a0f3099598ea2f187f803b8d66b328edf300720bfb016f4d89b4a1eceebf969f508080808080808080f89180a0ee5f307c063eefc1f9ad442f3b9f8f2981f9385b41da5465de5ac5dec863d5c7a0d5a8f8f4ab278e0aea28f1044da97c7bd3a5e807b48cd01bf705b704aa5ddd14a032a40b81b5316142b455addcb7bdd194be8e38196408efefcc4291803a402eeea0188088651f1f064c8fa57051108a83c9d695f1a124dc3783ed2a2e6e7c8fd21a808080808080808080808080f902ef20b902ebf902e801830743f9b9010000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000000800000000000000000080000010000000000000000000010000000008000000000000000000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000400020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000fd71dc9721d9ddcf0480a582927c3dcd42f3064ca00000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000af9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000fd71dc9721d9ddcf0480a582927c3dcd42f3064ca0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000005d17d8a0120000000000000000000000000000000000000000000000006f680513d061bb0d020000000000000000000000000000000000000000000001c57a98b6c5d67d41f500000000000000000000000000000000000000000000006f6804b6b8891afb020000000000000000000000000000000000000000000001c57a9913ddaf1d53f58200038000000000000000000000000000000000000000000000000000'
)


def test_withdraw_exit_return_tx(abi_manager, erc_20_parent):
    result = erc_20_parent.withdraw_exit(
        '0x1c20c41b9d97d1026aa456a21f13725df63edec1b1f43aacb180ebcc6340a2d3',
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'return_transaction': True, 'gas_limit': 200000},
    )
    print(len(exit_data))
    print(len(result['data']))
    assert result['data'] == exit_data

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


def test_withdraw_exit_faster_return_tx_without_set_proof_api(erc_20_parent):
    with pytest.raises(ProofAPINotSetException):
        erc_20_parent.withdraw_exit_faster(
            '0x1c20c41b9d97d1026aa456a21f13725df63edec1b1f43aacb180ebcc6340a2d3',
            '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
            {'return_transaction': True},
        )


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
        '0x1c20c41b9d97d1026aa456a21f13725df63edec1b1f43aacb180ebcc6340a2d3',
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
        {'return_transaction': True, 'gas_limit': 200000},
    )
    assert result['data'] == exit_data

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


@pytest.mark.skipif(os.getenv('TEST_ALL', 'False') != 'True', reason='Too hard')
def test_child_transfer(erc_20, erc_20_child, pos_client_for_to, to, from_):
    old_balance = erc_20_child.get_balance(to)
    amount = 10
    result = erc_20_child.transfer(
        amount,
        to,
        '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
    )

    tx_hash = result.transaction_hash
    print('Forward: ', tx_hash.hex())
    assert tx_hash

    tx_receipt = result.get_receipt(timeout=20 * 60)
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
    result = erc_20_child_token.transfer(
        amount,
        from_,
        'af024b43bcbe9aaaf44eb82f650896ede843ec014275297712d1653ad4caf57a',
    )
    print('Back: ', result.transaction_hash.hex())
    result.receipt


@pytest.mark.skipif(os.getenv('TEST_ALL', 'False') != 'True', reason='Too hard')
def test_approve(erc_20_parent):
    result = erc_20_parent.approve(10)
    tx_hash = result.get_transaction_hash()
    assert isinstance(tx_hash, str)

    tx_receipt = result.get_receipt()
    assert tx_receipt.type == 2


@pytest.mark.skipif(os.getenv('TEST_ALL', 'False') != 'True', reason='Too hard')
def test_deposit(erc_20_parent, from_):
    erc_20_parent.approve(10)
    result = erc_20_parent.deposit(10, from_)

    tx_hash = result.get_transaction_hash()
    assert isinstance(tx_hash, str)

    result.get_receipt()
    # assert(tx_receipt).to.be.an('object')
