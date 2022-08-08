import os

import pytest
from web3 import Web3


@pytest.fixture()
def rpc():
    return {
        'parent': os.getenv('ROOT_RPC', 'https://rpc-mumbai.maticvigil.com'),
        'child': os.getenv('MATIC_RPC') or 'https://rpc-mumbai.maticvigil.com',
    }


@pytest.fixture()
def pos():
    return {
        'parent': {
            'erc_20': Web3.toChecksumAddress(
                '0x3f152b63ec5ca5831061b2dccfb29a874c317502'
            ),
            # erc20: '0x655f2166b0709cd575202630952d71e2bb0d61af',
            'erc_721': Web3.toChecksumAddress(
                '0x16f7ef3774c59264c46e5063b1111bcfd6e7a72f'
            ),
            # erc721: '0x5a08d01e07714146747950CE07BB0f741445D1b8',
            'erc_1155': Web3.toChecksumAddress(
                '0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063'
            ),
            # Address of RootChainManager proxy for POS Portal
            'chain_manager_address': Web3.toChecksumAddress(
                '0xBbD7cBFA79faee899Eaf900F13C9065bF03B1A74'
            ),
        },
        'child': {
            'erc_721': Web3.toChecksumAddress(
                '0xbD88C3A7c0e242156a46Fbdf87141Aa6D0c0c649'
            ),
            # erc20: '0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1',
            'erc_20': Web3.toChecksumAddress(
                '0xA0D9f8282cD48d22Fd875E43Be32793124f8eD47'
            ),
            'weth': Web3.toChecksumAddress(
                '0x714550C2C1Ea08688607D86ed8EeF4f5E4F22323'
            ),
            'erc_1155': Web3.toChecksumAddress(
                '0xA07e45A987F19E25176c877d98388878622623FA'
            ),
        },
    }


@pytest.fixture()
def user1():
    return {
        'address': os.getenv(
            'USER1_FROM', '0x283759c017fa2B7095D408BDbd80EA6402C9c6cf'
        ),
        'private_key': os.getenv(
            'USER1_PRIVATE_KEY',
            '9cbbfc73c2ba01dc8d09deb3fd9c4abe27998ad40483c013f54367ae1f11da36',
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
            'af024b43bcbe9aaaf44eb82f650896ede843ec014275297712d1653ad4caf57a',
        ),
    }
