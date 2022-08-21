import pytest
from dotenv import load_dotenv

from matic.json_types import IPOSClientConfig, NeighbourClientConfig
from matic.pos import POSClient

load_dotenv()


@pytest.fixture()
def pos():
    return {
        'parent': {
            'erc_20': '0x655F2166b0709cd575202630952D71E2bB0d61Af',
            'erc_721': '0x02C869F27B0D09004107818B1150e354d38Cb189',
            'erc_1155': '0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063',
            'chain_manager_address': '0xBbD7cBFA79faee899Eaf900F13C9065bF03B1A74',
        },
        'child': {
            'erc_20': '0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1',
            'erc_721': '0xD6A8e816D2314E5635aB71991552A435c00B2952',
            'erc_1155': '0xA07e45A987F19E25176c877d98388878622623FA',
            'weth': '0xA6FA4fB5f76172d178d61B04b0ecd319C5d1C0aa',
        },
    }


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
def erc_20(pos):
    return {'parent': pos['parent']['erc_20'], 'child': pos['child']['erc_20']}


@pytest.fixture()
def erc_20_child(pos_client, erc_20):
    return pos_client.erc_20(erc_20['child'])


@pytest.fixture()
def erc_20_parent(pos_client, erc_20):
    return pos_client.erc_20(erc_20['parent'], True)


@pytest.fixture()
def erc_721(pos):
    return {'parent': pos['parent']['erc_721'], 'child': pos['child']['erc_721']}


@pytest.fixture()
def erc_721_child(pos_client, erc_721):
    return pos_client.erc_721(erc_721['child'])


@pytest.fixture()
def erc_721_parent(pos_client, erc_721):
    return pos_client.erc_721(erc_721['parent'], True)


@pytest.fixture()
def erc_1155(pos):
    return {'parent': pos['parent']['erc_1155'], 'child': pos['child']['erc_1155']}


@pytest.fixture()
def erc_1155_child(pos_client, erc_1155):
    return pos_client.erc_1155(erc_1155['child'])


@pytest.fixture()
def erc_1155_parent(pos_client, erc_1155):
    return pos_client.erc_1155(erc_1155['parent'], True)
