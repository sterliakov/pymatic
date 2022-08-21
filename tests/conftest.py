import os

import pytest
from dotenv import load_dotenv
from web3 import Web3

from matic.utils.abi_manager import ABIManager

load_dotenv()


@pytest.fixture()
def rpc():
    return {
        'parent': os.getenv(
            'ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
        ),
        'child': os.getenv('MATIC_RPC', 'https://rpc-mumbai.maticvigil.com'),
    }


@pytest.fixture()
def user1():
    return {
        'address': os.getenv('USER1_FROM'),
        'private_key': os.getenv('USER1_PRIVATE_KEY'),
    }


@pytest.fixture()
def user2():
    return {
        'address': os.getenv('USER2_FROM'),
        'private_key': os.getenv('USER2_PRIVATE_KEY'),
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
def abi_manager():
    return ABIManager('testnet', 'mumbai')
