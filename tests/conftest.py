import os

import pytest
from web3 import Web3


@pytest.fixture()
def rpc():
    return {
        'parent': os.getenv(
            'ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
        ),
        'child': os.getenv('MATIC_RPC')
        or 'https://rpc-mumbai.maticvigil.com/v1/2029c255385562b351f79af8f40c51d85b97d757',
    }


@pytest.fixture()
def pos():
    return {
        'parent': {
            # 'erc_20': Web3.toChecksumAddress(
            #     '0x3f152b63ec5ca5831061b2dccfb29a874c317502'.lower()
            # ),
            'erc_20': Web3.toChecksumAddress(
                '0x655f2166b0709cd575202630952d71e2bb0d61af'.lower()
            ),
            # 'erc_721': Web3.toChecksumAddress(
            #     '0x16f7ef3774c59264c46e5063b1111bcfd6e7a72f'.lower()
            # ),
            'erc_721': Web3.toChecksumAddress(
                '0x084297B12F204Adb74c689be08302FA3f12dB8A7'.lower()
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
            # 'erc_20': Web3.toChecksumAddress(
            #     '0xA0D9f8282cD48d22Fd875E43Be32793124f8eD47'.lower()
            # ),
            'erc_20': Web3.toChecksumAddress(
                '0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1'.lower()
            ),
            # 'erc_721': Web3.toChecksumAddress(
            #     '0xbD88C3A7c0e242156a46Fbdf87141Aa6D0c0c649'.lower()
            # ),
            'erc_721': Web3.toChecksumAddress(
                '0x757b1BD7C12B81b52650463e7753d7f5D0565C0e'.lower()
            ),
            'erc_1155': Web3.toChecksumAddress(
                '0xA07e45A987F19E25176c877d98388878622623FA'.lower()
            ),
            # 'weth': Web3.toChecksumAddress(
            #     '0x714550C2C1Ea08688607D86ed8EeF4f5E4F22323'.lower()
            # ),
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
