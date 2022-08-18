import os

import pytest
from web3 import Web3

from matic.json_types import IPOSClientConfig, NeighbourClientConfig
from matic.pos import POSClient
from matic.utils.abi_manager import ABIManager


@pytest.fixture()
def rpc():
    return {
        'parent': os.getenv(
            'ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
        ),
        'child': os.getenv('MATIC_RPC', 'https://rpc-mumbai.maticvigil.com'),
    }


@pytest.fixture()
def pos():
    return {
        'parent': {
            'erc_20': Web3.toChecksumAddress(
                '0x655f2166b0709cd575202630952d71e2bb0d61af'.lower()
            ),
            'erc_721': Web3.toChecksumAddress(
                '0x02C869F27B0D09004107818B1150e354d38Cb189'.lower()
            ),
            'erc_1155': Web3.toChecksumAddress(
                '0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063'.lower()
            ),
            # Address of RootChainManager proxy for POS Portal
            'chain_manager_address': Web3.toChecksumAddress(
                '0xBbD7cBFA79faee899Eaf900F13C9065bF03B1A74'.lower()
            ),
        },
        'child': {
            'erc_20': Web3.toChecksumAddress(
                '0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1'.lower()
            ),
            'erc_721': Web3.toChecksumAddress(
                '0xD6A8e816D2314E5635aB71991552A435c00B2952'.lower()
            ),
            'erc_1155': Web3.toChecksumAddress(
                '0xA07e45A987F19E25176c877d98388878622623FA'.lower()
            ),
            'weth': Web3.toChecksumAddress(
                '0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa'.lower()
            ),
        },
    }


@pytest.fixture()
def user1():
    return {
        'address': os.getenv(
            'USER1_FROM', '0xD73a10cEFa7cF0FA3ae4855b13317Ee77B0Ef9c1'
        ),
        'private_key': os.getenv(
            'USER1_PRIVATE_KEY',
            '0x80f6cbad3710a839382acea3168e638f6c1007e1210103c10874e4653420ca79',
        ),
    }


@pytest.fixture()
def user2():
    return {
        'address': os.getenv(
            'USER2_FROM', '0xa315B75bf9ED0F2b82d5193c83aEcda10d81fE7d'
        ),  # Your address
        'private_key': os.getenv(
            'USER2_PRIVATE_KEY',
            '0xaf024b43bcbe9aaaf44eb82f650896ede843ec014275297712d1653ad4caf57a',
        ),
    }


@pytest.fixture()
def from_pk(user1):
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
def pos_client(user1, parent_provider, child_provider):
    return POSClient(
        IPOSClientConfig(
            network='testnet',
            version='mumbai',
            parent=NeighbourClientConfig(
                provider=parent_provider,
                default_config={'from': user1['address']},
            ),
            child=NeighbourClientConfig(
                provider=child_provider,
                default_config={'from': user1['address']},
            ),
        )
    )


@pytest.fixture()
def pos_client_for_to(user2, parent_provider, child_provider):
    return POSClient(
        IPOSClientConfig(
            network='testnet',
            version='mumbai',
            parent=NeighbourClientConfig(
                provider=parent_provider,
                default_config={'from': user2['address']},
            ),
            child=NeighbourClientConfig(
                provider=child_provider,
                default_config={'from': user2['address']},
            ),
        )
    )


@pytest.fixture()
def abi_manager():
    return ABIManager('testnet', 'mumbai')
