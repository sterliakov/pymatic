import pytest
from dotenv import load_dotenv

from matic.json_types import IPlasmaClientConfig, NeighbourClientConfig
from matic.plasma import PlasmaClient

load_dotenv()


@pytest.fixture()
def plasma():
    return {
        'parent': {
            'erc_20': '0x3f152B63Ec5CA5831061B2DccFb29a874C317502',
            'erc_721': '0xfA08B72137eF907dEB3F202a60EfBc610D2f224b',
            'matic': '0x499d11E0b6eAC7c0593d8Fb292DCBbF815Fb29Ae',
        },
        'child': {
            'erc_20': '0x2d7882beDcbfDDce29Ba99965dd3cdF7fcB10A1e',
            'erc_721': '0x33FC58F12A56280503b04AC7911D1EceEBcE179c',
            'matic': '0x0000000000000000000000000000000000001010',
        },
    }


@pytest.fixture()
def plasma_client(user1, parent_provider, child_provider):
    return PlasmaClient(
        IPlasmaClientConfig(
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
def plasma_client_for_to(user2, parent_provider, child_provider):
    return PlasmaClient(
        IPlasmaClientConfig(
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
def erc_20(plasma):
    return {
        'parent': plasma['parent']['erc_20'],
        'child': plasma['child']['erc_20'],
        'matic': plasma['parent']['matic'],
        'matic_child': plasma['child']['matic'],
    }


@pytest.fixture()
def erc_20_child(plasma_client, erc_20):
    return plasma_client.erc_20(erc_20['child'])


@pytest.fixture()
def erc_20_parent(plasma_client, erc_20):
    return plasma_client.erc_20(erc_20['parent'], True)


@pytest.fixture()
def erc_20_matic_child(plasma_client: PlasmaClient, erc_20):
    return plasma_client.erc_20(None)


@pytest.fixture()
def erc_20_matic_parent(plasma_client: PlasmaClient, erc_20):
    return plasma_client.erc_20(erc_20['matic'], True)


@pytest.fixture()
def erc_721(plasma):
    return {
        'parent': plasma['parent']['erc_721'],
        'child': plasma['child']['erc_721'],
    }


@pytest.fixture()
def erc_721_child(plasma_client, erc_721):
    return plasma_client.erc_721(erc_721['child'])


@pytest.fixture()
def erc_721_parent(plasma_client, erc_721):
    return plasma_client.erc_721(erc_721['parent'], True)
