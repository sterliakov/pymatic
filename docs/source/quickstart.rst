Initial setup
===============================

Configuration
-------------

To proceed with testing, you'll need environment configuration based on the following template:

.. code-block:: bash

    USER1_FROM=  # 0x...
    USER1_PRIVATE_KEY=  # Without prefix
    USER2_FROM=  # 0x...
    USER2_PRIVATE_KEY=  # Without prefix

    ROOT_RPC=https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161
    MATIC_RPC=https://rpc-mumbai.maticvigil.com
    PROOF_API=https://apis.matic.network/api/v1/

The RPC provided can be used as-is for testnet (Mumbai - child chain, Goerli - parent chain).

To run any of test examples, you'll need two addresses. **Don't use real addresses on testnet!**

Then, to execute any transactions you'll need some MATIC tokens. You can obtain them via the `Polygon faucet`_ (better - for both addresses, so you don't think later how to transfer something back).

To power transactions originating from parent chain, you'll need some Goerli ETH. You can obtain them via `Goerli faucet <https://goerlifaucet.com/>`_.

Basic usage: clients
--------------------

.. Note::

    You can also adjust ABI url used by this library. You can do it in any of two ways:

    - Set environmental variable (``export MATIC_ABI_STORE=...`` or via .env file, if you load it);
    - Set value in python code directly::

        from matic import services
        services.DEFAULT_ABI_STORE_URL = '...'
        # See .env.example for one of possible URLs

.. Warning::

    In order to use methods of ``withdraw_exit_faster`` family, you need to set default proof API URI. You can do it in any of two ways:

    - Set environmental variable (``export MATIC_PROOF_API=...`` or via .env file, if you load it);
    - Set value in python code directly::

        from matic import services
        services.DEFAULT_PROOF_API_URL = '...'
        # See .env.example for one of possible URLs

You can create a client to interact with blockchain like in the following snippet:

.. code-block:: python

    #!/usr/bin/env python

    import os

    from dotenv import load_dotenv
    from matic import POSClient
    from web3 import Web3

    load_dotenv()

    from_ = os.getenv('USER1_FROM')
    from_pk = os.getenv('USER1_PRIVATE_KEY')

    parent_contract = '0x02C869F27B0D09004107818B1150e354d38Cb189'
    rpc_parent = os.getenv('ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161')
    rpc_child = os.getenv('MATIC_RPC', 'https://rpc-mumbai.maticvigil.com')

    pos_client = POSClient({
        'network': 'testnet',
        'version': 'mumbai',
        'parent': {
            'provider': Web3.HTTPProvider(rpc_parent),
            'default_config': {'from': from_},
        },
        'child': {
            'provider': Web3.HTTPProvider(rpc_child),
            'default_config': {'from': from_},
        },
    })

Obtaining tokens
----------------

If you want to experiment with dummy tokens, read the following sections on how to obtain them.

POS bridge tokens
~~~~~~~~~~~~~~~~~

POS ERC20
^^^^^^^^^

ERC20 token used in this tutorial is "Dummy ERC20 (DERC20)".

Mapped contracts:

- parent: `0x655F2166b0709cd575202630952D71E2bB0d61Af <https://goerli.etherscan.io/address/0x655F2166b0709cd575202630952D71E2bB0d61Af>`_
- child: `0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1 <https://mumbai.polygonscan.com/address/0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1>`_

You can obtain them via the `Polygon faucet`_. To avoid resolving unexpected "insufficient balance" errors in future, get this token both on Mumbai and Goerli testnets.

POS ERC721
^^^^^^^^^^

We use "Test ERC721 (DERC721)" as a ERC721 token example.

Mapped contracts:

- parent: `0x02C869F27B0D09004107818B1150e354d38Cb189 <https://goerli.etherscan.io/address/0x02c869f27b0d09004107818b1150e354d38cb189>`_
- child: `0xD6A8e816D2314E5635aB71991552A435c00B2952 <https://mumbai.polygonscan.com/address/0xD6A8e816D2314E5635aB71991552A435c00B2952>`_


This is perhaps the most difficult token to obtain.

- First, mint them on Goerli (you can do it directly from `explorer <https://goerli.etherscan.io/address/0x02C869F27B0D09004107818B1150e354d38Cb189#writeContract>`_, if you're using browser-syncable wallet like metamask, or by interacting with contract by any convenient tool of your choice). They are not divisible, so every transaction uses 1 or more tokens, and you mint 1 at a time. Mint as many as you need.
- Then, deposit these tokens to Mumbai testnet. You can use the following script to do so:

.. code-block:: python

    #!/usr/bin/env python

    import os

    from dotenv import load_dotenv
    from matic import POSClient
    from web3 import Web3

    load_dotenv()

    from_ = os.getenv('USER1_FROM')
    from_pk = os.getenv('USER1_PRIVATE_KEY')

    parent_contract = '0x02C869F27B0D09004107818B1150e354d38Cb189'
    rpc_parent = os.getenv('ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161')
    rpc_child = os.getenv('MATIC_RPC', 'https://rpc-mumbai.maticvigil.com')

    pos_client = POSClient({
        'network': 'testnet',
        'version': 'mumbai',
        'parent': {
            'provider': Web3.HTTPProvider(rpc_parent),
            'default_config': {'from': from_},
        },
        'child': {
            'provider': Web3.HTTPProvider(rpc_child),
            'default_config': {'from': from_},
        },
    })

    erc_721_parent = pos_client.erc_721(parent_contract, True)

    tokens = erc_721_parent.get_all_tokens(from_)

    approve_tx = erc_721_parent.approve_all(from_pk)
    assert approve_tx.receipt

    # You can use only some of the tokens here to preserve something on parent chain too.
    deposit_tx = erc_721_parent.deposit_many(tokens, from_, from_pk)
    print(deposit_tx.transaction_hash)
    assert deposit_tx.receipt

You can wait for these tokens to be added with ``pos_client.is_deposited(transaction_hash)`` or just monitor your balance with your wallet or an explorer.

If you've spent all of the tokens, you can mint a couple more.

POS ERC1155
^^^^^^^^^^^

We use "Test ERC1155 (DERC1155)" as a ERC1155 token example.

Mapped contracts:

- parent: `0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063 <https://goerli.etherscan.io/address/0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063>`_
- child: `0xA07e45A987F19E25176c877d98388878622623FA <https://mumbai.polygonscan.com/address/0xA07e45A987F19E25176c877d98388878622623FA>`_

You can obtain tokens on both testnets via the `Polygon faucet`_.

.. _Polygon faucet: https://faucet.polygon.technology/


Plasma bridge tokens
~~~~~~~~~~~~~~~~~~~~

Plasma ERC20
^^^^^^^^^^^^

Mapped contracts:

- parent: `0x3f152B63Ec5CA5831061B2DccFb29a874C317502 <https://goerli.etherscan.io/address/0x3f152B63Ec5CA5831061B2DccFb29a874C317502>`_
- child: `0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1 <https://mumbai.polygonscan.com/address/0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1>`_

You can obtain them via the `Polygon faucet`_. To avoid resolving unexpected "insufficient balance" errors in future, get this token both on Mumbai and Goerli testnets.

Plasma ERC721
^^^^^^^^^^^^^

Mapped contracts:

- parent: `0xfA08B72137eF907dEB3F202a60EfBc610D2f224b <https://goerli.etherscan.io/address/0xfA08B72137eF907dEB3F202a60EfBc610D2f224b>`_
- child: `0x33FC58F12A56280503b04AC7911D1EceEBcE179c <https://mumbai.polygonscan.com/address/0x33FC58F12A56280503b04AC7911D1EceEBcE179c>`_


This is another token which is difficult to obtain.

- First, mint them on Goerli (you can do it directly from `chain explorer <https://goerli.etherscan.io/address/0xfA08B72137eF907dEB3F202a60EfBc610D2f224b#writeContract>`_, if you're using browser-syncable wallet like metamask, or by interacting with contract by any convenient tool of your choice). They are not divisible, so every transaction uses 1 or more tokens, and you mint 1 at a time. Mint as many as you need.
- Then, deposit these tokens to Mumbai testnet. You can use the following script to do so:

.. code-block:: python

    #!/usr/bin/env python

    import os
    import time

    from dotenv import load_dotenv
    from matic import PlasmaClient
    from web3 import Web3

    load_dotenv()

    from_ = os.getenv('USER1_FROM')
    from_pk = os.getenv('USER1_PRIVATE_KEY')

    parent_contract = '0x02C869F27B0D09004107818B1150e354d38Cb189'
    rpc_parent = os.getenv('ROOT_RPC', 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161')
    rpc_child = os.getenv('MATIC_RPC', 'https://rpc-mumbai.maticvigil.com')

    plasma_client = PlasmaClient({
        'network': 'testnet',
        'version': 'mumbai',
        'parent': {
            'provider': Web3.HTTPProvider(rpc_parent),
            'default_config': {'from': from_},
        },
        'child': {
            'provider': Web3.HTTPProvider(rpc_child),
            'default_config': {'from': from_},
        },
    })

    erc_721_parent = pos_client.erc_721(parent_contract, True)

    token = erc_721_parent.get_all_tokens(from_, 1)[0]

    deposit_tx = erc_721_parent.safe_deposit(
        token, from_, from_pk, {'gas_limit': 300_000}
    )
    assert deposit_tx.receipt.status
    tx_hash = deposit_tx.transaction_hash

    start_time = time.time()
    timeout = 60 * 60
    while True:
        if plasma_client.is_deposited(tx_hash):
            break
        elif time.time() - start_time > timeout:
            print(f'Transaction {tx_hash.hex()} still not deposited')
        else:
            time.sleep(30)


You can wait for these tokens to be added with ``pos_client.is_deposited(transaction_hash)`` or just monitor your balance with your wallet or an explorer.

If you've spent all of the tokens, you can mint a couple more.
