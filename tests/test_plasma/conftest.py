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
            'erc_20': '0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1',
            'erc_721': '0x33FC58F12A56280503b04AC7911D1EceEBcE179c',
            'matic': '0x0000000000000000000000000000000000001010',
        },
        'registry_address': '0x56B082d0a590A7ce5d170402D6f7f88B58F71988',
        # The address for the main Plasma contract in  Ropsten testnet
        'root_chain_address': '0x82a72315E16cE224f28E1F1fB97856d3bF83f010',
        # An address for the WithdrawManager contract on Ropsten testnet
        'withdraw_manager_address': '0x3cf9aD3395028a42EAfc949e2EC4588396b8A7D4',
        # An address for a DepositManager contract in Ropsten testnet
        'deposit_manager_address': '0x3Bc6701cA1C32BBaC8D1ffA2294EE3444Ad93989',
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
