Plasma bridge
=============

Read `Getting started <https://docs.polygon.technology/docs/develop/ethereum-polygon/plasma/getting-started>`_ for more info.

.. Note::

    Just in case you wanna do it: you can adjust used client implementations.

    .. code-block:: python

        from matic import utils
        from myimpl import MyOtherWeb3ClientClass

        utils.Web3Client = MyOtherWeb3ClientClass

    This client must conform with existing :class:`~matic.abstracts.BaseWeb3Client` (and use implementations of other abstracts from that file).


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

Bridge
------
.. automodule:: matic.plasma

ERC 20 tokens
-------------
.. automodule:: matic.plasma.erc_20

ERC 721 tokens
--------------

.. Warning::
    Please don't feel upset if you cannot withdraw ERC-721 from Mumbai to Goerli. I cannot too.

    ``ERC721PredicateBurnOnly`` contract was deployed with wrong (?) ``WithdrawManager`` address
    (see `on etherscan <https://goerli.etherscan.io/address/0x473cb675c9214f79dee10948443509c441a678e7#code>`_), so all transactions with ``WithdrawManager`` for ERC721 fail.

    I tried deploying separate contract with this fixed (just a copy via Remix),
    and everything is OK until ``checkPredicateAndTokenMapping`` modifier check fires
    on ``WithdrawManager`` (and this failure is 100% valid, since my contract is not
    acknowledged as proper ERC721 predicate). Proper addresses are ``DepositManagerProxy`` and ``WithdrawManagerProxy`` values from `ABI index <https://static.matic.network/network/testnet/mumbai/index.json>`_.

    For further investigation, contracts can be found in `this repo <https://github.com/maticnetwork/contracts/blob/main/contracts/>`_.

.. automodule:: matic.plasma.erc_721

Helper contracts interaction
----------------------------
.. automodule:: matic.plasma.contracts

Base plasma token
-----------------
.. automodule:: matic.plasma.plasma_token
