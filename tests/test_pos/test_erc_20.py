from __future__ import annotations

import pytest
from eth_typing import HexAddress, HexStr

from matic import logger, services
from matic.exceptions import NullSpenderAddressException, ProofAPINotSetException
from matic.pos import ERC20, POSClient
from matic.utils.abi_manager import ABIManager

from ..conftest import DEFAULT_PROOF_API_URL

WITHDRAW_EXITED_TX_HASH = bytes.fromhex(
    'd6f7f4c6052611761946519076de28fbd091693af974e7d4abc1b17fd7926fd7'
)


@pytest.mark.read()
def test_get_balance_child(erc_20_child: ERC20, from_: HexAddress):
    balance = erc_20_child.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_balance_parent(erc_20_parent: ERC20, from_: HexAddress):
    balance = erc_20_parent.get_balance(from_)
    assert isinstance(balance, int)
    assert balance > 0


@pytest.mark.read()
def test_get_allowance_child(erc_20_child: ERC20, from_: HexAddress):
    allowance = erc_20_child.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


@pytest.mark.read()
def test_get_allowance_parent(erc_20_parent: ERC20, from_: HexAddress):
    allowance = erc_20_parent.get_allowance(from_)
    assert isinstance(allowance, int)
    assert allowance >= 0


@pytest.mark.read()
def test_is_checkpointed(pos_client: POSClient):
    assert pos_client.is_checkpointed(WITHDRAW_EXITED_TX_HASH) is True


@pytest.mark.read()
def test_is_withdraw_exited(erc_20_parent: ERC20):
    assert erc_20_parent.is_withdraw_exited(WITHDRAW_EXITED_TX_HASH) is True


@pytest.mark.read()
def test_call_get_block_included():
    result = services.get_block_included('testnet', 1000)
    assert isinstance(result.start, int)
    assert isinstance(result.end, int)
    assert isinstance(result.header_block_number, int)
    assert result.proposer.startswith('0x')
    assert result.root.startswith('0x')
    assert result.block_number == 1000
    assert isinstance(result.created_at, int)


@pytest.mark.read()
def test_is_deposited(pos_client: POSClient):
    tx_hash = bytes.fromhex(
        'c67599f5c967f2040786d5924ec55d37bf943c009bdd23f3b50e5ae66efde258'
    )
    is_deposited = pos_client.is_deposited(tx_hash)
    assert is_deposited is True


@pytest.mark.offline()
def test_child_transfer_return_transaction_with_erp_1159(
    erc_20_child: ERC20, to: HexAddress, from_pk: HexStr
):
    amount = 1
    # Using enormous max_fee_per_gas, otherwise this test sometimes fails with
    # > max fee per gas less than block base fee:
    # > address ***, maxFeePerGas: 30 baseFee: 879 (supplied gas 10010499)'}
    result = erc_20_child.transfer(
        amount,
        to,
        from_pk,
        {
            'max_fee_per_gas': 1000,
            'max_priority_fee_per_gas': 1000,
            'gas_limit': 120_000,
            'return_transaction': True,
        },
    ).transaction_config
    assert result['max_fee_per_gas'] == 1000
    assert result['max_priority_fee_per_gas'] == 1000
    assert 'gas_price' not in result
    assert result['chain_id'] == 80001


@pytest.mark.offline()
def test_child_transfer_return_transaction(
    erc_20_child: ERC20, to: HexAddress, from_: HexAddress, from_pk: HexStr, erc_20
):
    amount = 1
    result = erc_20_child.transfer(
        amount,
        to,
        from_pk,
        {'return_transaction': True},
    ).transaction_config
    assert result['chain_id'] == 80001
    assert result['to'] == erc_20['child']
    assert result['from'] == from_
    assert result['value'] == 0


@pytest.mark.offline()
def test_parent_transfer_return_transaction_with_erp_1159(
    erc_20_parent: ERC20, to: HexAddress, from_pk: HexStr
):
    amount = 1
    result = erc_20_parent.transfer(
        amount,
        to,
        from_pk,
        {
            'max_fee_per_gas': 80,
            'max_priority_fee_per_gas': 80,
            'gas_limit': 120_000,
            'return_transaction': True,
        },
    ).transaction_config

    assert result['max_fee_per_gas'] == 80
    assert result['max_priority_fee_per_gas'] == 80
    assert 'gas_price' not in result
    assert result['chain_id'] == 5


@pytest.mark.offline()
def test_withdraw_start_return_tx(erc_20, erc_20_child: ERC20, from_pk: HexStr):
    result = erc_20_child.withdraw_start(
        10, from_pk, {'return_transaction': True}
    ).transaction_config

    assert result['to'].lower() == erc_20['child'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_parent_return_tx(erc_20, erc_20_parent: ERC20, from_pk: HexStr):
    result = erc_20_parent.approve(
        10,
        from_pk,
        {'return_transaction': True},
    ).transaction_config

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_parent_return_tx_with_spender_address(
    erc_20, erc_20_parent: ERC20, from_pk: HexStr
):
    spender_address = erc_20_parent.predicate_address
    result = erc_20_parent.approve(
        1,
        from_pk,
        {'spender_address': spender_address, 'return_transaction': True},
    ).transaction_config

    assert result['to'].lower() == erc_20['parent'].lower()
    assert 'data' in result


@pytest.mark.offline()
def test_approve_child_return_tx_without_spender_address(
    erc_20, erc_20_child: ERC20, from_pk: HexStr
):
    with pytest.raises(NullSpenderAddressException):
        erc_20_child.approve(1, from_pk)


@pytest.mark.offline()
def test_deposit_return_tx(
    abi_manager: ABIManager, erc_20_parent: ERC20, from_: HexAddress, from_pk: HexStr
):
    result = erc_20_parent.deposit(
        9, from_, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


exit_data = bytes.fromhex(
    '3805550f00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000741f9073e8423d1ec00b90100607e346e173cb8dcb5786265cc1264562462e3d0d4a14122bc088c6e35c23167a1c79f16dc17a2aaab85e5f759e18a40db750f262155e489c5f9b8dfa759ef1cea7fbf33ba48e44e44e2e2b5ca8a61bb32bcb7f14f7eb7e853f6698681a0356d564de85c8772fbd0b15dce8168ef9965d53cef0947d80fe8e3d562c5fccdffa89bf8ddfc998afe2723c5f99b9cca0c960953809513203979e077808d59620556fd0bb97fc4896508954b02c19b90fd244a391e50fe0cd6b979ff1afa1ac2a2e6432bcb168e3932a52c0d460fb2e93a4fc730e5bd0ccc9e42c2755a04a0800bc70068067197f28641cdbdf52915e48cc4eb65a6a74b37694bbee0ad96ce46751984013f8974846180c3c8a01c231c504b86cd2bbf2360e61bf747207ee2fbfc6f35005c328005c600e9255ca0ea31d8804cd84c283be9702b4de7eff615884681cc7c4cfdc65a46673eeb566cb902eaf902e701828547b9010000000000400000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000001800000000000000000080000010000000000000000000010000000000000000000000040000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000000020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a00000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000011f9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000007c1fcb8018000000000000000000000000000000000000000000000000056bc077dda68980000000000000000000000000000000000000000000000001ded4a9e3b2e378e3ca0000000000000000000000000000000000000000000000056bbffbbddb0968000000000000000000000000000000000000000000000001ded4aa5fd2aef8fbcab902f6f902f3f902f0822080b902eaf902e701828547b9010000000000400000020000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000008000000800000000000000000000100000000000000000000020000000000000000001800000000000000000080000010000000000000000000010000000000000000000000040000000000000000000000000000200000000000000020000000000000010001000000000000000000000000004000000003000000000001000000000000000000000000000000100000000020000000000000000000000000000000000000000000000000000000000000100000f901ddf89b94fe4f5145f6e09952a5ba9e956ed0c25e3fa4c7f1f863a0ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3efa0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a00000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000011f9013d940000000000000000000000000000000000001010f884a04dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63a00000000000000000000000000000000000000000000000000000000000001010a0000000000000000000000000bbca830ee5dcabde33db24496b5524b9c5a69fe6a0000000000000000000000000c26880a0af2ea0c7e8130e6ec47af756465452e8b8a000000000000000000000000000000000000000000000000000007c1fcb8018000000000000000000000000000000000000000000000000056bc077dda68980000000000000000000000000000000000000000000000001ded4a9e3b2e378e3ca0000000000000000000000000000000000000000000000056bbffbbddb0968000000000000000000000000000000000000000000000001ded4aa5fd2aef8fbca8200808000000000000000000000000000000000000000000000000000000000000000'  # noqa: E501
)
EXITED_TX_HASH = bytes.fromhex(
    'b005d8db45f33836c422ee18286fa8ebe49b4ec7b9930e673d85ecd081cc3b8e'
)


@pytest.mark.offline()
def test_withdraw_exit_return_tx(
    abi_manager: ABIManager, erc_20_parent: ERC20, from_pk: HexStr
):
    result = erc_20_parent.withdraw_exit(
        EXITED_TX_HASH,
        from_pk,
        {'return_transaction': True, 'gas_limit': 200_000},
    ).transaction_config
    assert result['data'].hex() == exit_data.hex()

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


@pytest.mark.offline()
def test_withdraw_exit_faster_return_tx_without_set_proof_api(
    erc_20_parent: ERC20, from_pk: HexStr
):
    services.DEFAULT_PROOF_API_URL = ''  # Without initialization it's empty string
    try:
        with pytest.raises(ProofAPINotSetException):
            erc_20_parent.withdraw_exit_faster(
                EXITED_TX_HASH,
                from_pk,
                {'return_transaction': True, 'gas_limit': 200_000},
            )
    finally:
        services.DEFAULT_PROOF_API_URL = DEFAULT_PROOF_API_URL


@pytest.mark.offline()
def test_withdraw_exit_faster_return_tx(
    abi_manager: ABIManager, erc_20_parent: ERC20, from_pk: HexStr
):
    result = erc_20_parent.withdraw_exit_faster(
        EXITED_TX_HASH, from_pk, {'return_transaction': True, 'gas_limit': 200_000}
    ).transaction_config
    assert result['data'].hex() == exit_data.hex()

    root_chain_manager = abi_manager.get_config(
        'Main.POSContracts.RootChainManagerProxy'
    )
    assert result['to'].lower() == root_chain_manager.lower()


@pytest.mark.online()
def test_child_transfer(
    erc_20,
    erc_20_child: ERC20,
    pos_client_for_to: POSClient,
    to: HexAddress,
    from_: HexAddress,
    from_pk: HexStr,
    to_private_key: HexStr,
):
    old_balance = erc_20_child.get_balance(to)
    amount = 10
    result = erc_20_child.transfer(amount, to, from_pk, {'gas_limit': 300_000})

    tx_hash = result.transaction_hash
    assert tx_hash
    logger.info('Forward: %s', tx_hash.hex())

    tx_receipt = result.get_receipt(timeout=5 * 60)
    assert tx_receipt
    assert tx_receipt.transaction_hash == tx_hash
    assert tx_receipt.from_.lower() == from_.lower()
    assert tx_receipt.to.lower() == erc_20['child'].lower()
    assert tx_receipt.type == '0x2'
    assert tx_receipt.gas_used > 0
    assert tx_receipt.cumulative_gas_used > 0
    assert tx_receipt.block_hash
    assert tx_receipt.block_number
    assert tx_receipt.logs_bloom
    assert tx_receipt.status

    new_balance = erc_20_child.get_balance(to)

    assert new_balance == old_balance + amount
    # transfer money back to user
    erc_20_child_token = pos_client_for_to.erc_20(erc_20['child'])
    result = erc_20_child_token.transfer(
        amount, from_, to_private_key, {'gas_limit': 300_000}
    )
    logger.info('Back: %s', result.transaction_hash.hex())
    result.receipt


@pytest.mark.online()
def test_deposit_ether(pos_client: POSClient, from_: HexAddress, from_pk: HexStr):
    res = pos_client.deposit_ether(1, from_, from_pk, {})
    assert res.receipt.status
