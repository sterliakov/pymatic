POS bridge
==========

Read `Getting started <https://docs.polygon.technology/docs/develop/ethereum-polygon/pos/getting-started>`_ for more info.

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

Bridge client
-------------
.. automodule:: matic.pos

ERC 20
------
.. automodule:: matic.pos.erc_20

ERC 721
-------
.. automodule:: matic.pos.erc_721

ERC 1155
--------
.. automodule:: matic.pos.erc_1155

Root chain
----------
.. automodule:: matic.pos.root_chain

Root chain manager
------------------
.. automodule:: matic.pos.root_chain_manager

Helper classes
--------------

Exit data building
^^^^^^^^^^^^^^^^^^
.. automodule:: matic.pos.exit_util

Base POS token
^^^^^^^^^^^^^^
.. automodule:: matic.pos.pos_token
