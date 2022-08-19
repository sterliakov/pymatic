[![PyPi Version](https://img.shields.io/pypi/v/matic.svg)](https://pypi.python.org/pypi/matic/)
[![Python Versions](https://img.shields.io/pypi/pyversions/matic.svg)](https://pypi.python.org/pypi/matic/)
[![Read the Docs](https://readthedocs.org/projects/pymatic/badge/?version=latest)](https://pymatic.readthedocs.io/en/latest/?badge=latest)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-blue-blue.svg)](https://blue.readthedocs.io/)


# Matic - Python SDK to assist developers on Polygon blockchain.

**Disclaimer: this package is not officialy maintained by Polygon affiliates.**

Read our [documentation](https://readthedocs.org/projects/pymatic/badge/?version=latest) on ReadTheDocs.

This project is a direct python port of [matic.js](https://github.com/maticnetwork/matic.js/) library. It includes also [maticjs-web3](https://github.com/maticnetwork/maticjs-web3/) port.

This library is very new, so documentation improvement is currently in progress. Please refer to official js SDK [docs](https://docs.polygon.technology/docs/develop/) for more comprehensive tutorials.


# Installation

Install with pip:

```bash
pip install -U matic
```

Install from source:

```bash
git clone https://github.com/sterliakov/pymatic/
cd pymatic
pip install .
```

Supported extras:

- `test`: install test and development dependencies (`pip install matic[test]`)
- `docs`: dependencies for building documentation (`pip install matic[docs]`)


# Obtaining tokens: initial setup

To proceed woth testing, you'll need environment configuration based on the following template:

```bash
USER1_FROM=  # 0x...
USER1_PRIVATE_KEY=  # Without prefix
USER2_FROM=  # 0x...
USER2_PRIVATE_KEY=  # Without prefix

ROOT_RPC=https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161
MATIC_RPC=https://rpc-mumbai.maticvigil.com
PROOF_API=https://apis.matic.network/api/v1/
```

The RPC provided can be used as-is for testnet (Mumbai - child chain, Goerli - parent chain).

To run any of test examples, you'll need two addresses. **Don't use real addresses on testnet!**

Then, to execute any transactions you'll need some MATIC tokens. You can obtain them via the [polygon faucet](https://faucet.polygon.technology/) (better - for both addresses, so you don't think later how to transfer something back).

To power transactions originating from parent chain, you'll need some Goerli ETH. You can obtain them via [this faucet](https://goerlifaucet.com/).

If you want to experiment with dummy tokens, read the following sections on how to obtain them.

## ERC20

ERC20 token used in this tutorial is "Dummy ERC20 (DERC20)".

Mapped contracts:
- parent: [0x655F2166b0709cd575202630952D71E2bB0d61Af](https://goerli.etherscan.io/address/0x655F2166b0709cd575202630952D71E2bB0d61Af)
- child: [0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1](https://mumbai.polygonscan.com/address/0xfe4F5145f6e09952a5ba9e956ED0C25e3Fa4c7F1)

You can obtain them via the [polygon faucet](https://faucet.polygon.technology/). To avoid resolving unexpected "insufficient balance" errors in future, get this token both on Mumbai and Goerli testnets.

## ERC721

We use "Test ERC721 (DERC721)" as a ERC721 token example.

Mapped contracts:
- parent: [0x02C869F27B0D09004107818B1150e354d38Cb189](https://goerli.etherscan.io/address/0x02C869F27B0D09004107818B1150e354d38Cb189)
- child: [0xD6A8e816D2314E5635aB71991552A435c00B2952](https://mumbai.polygonscan.com/address/0xD6A8e816D2314E5635aB71991552A435c00B2952)


This is perhaps the most difficult token to obtain.

* First, mint them on Goerli (you can do it [directly from explorer](https://goerli.etherscan.io/address/0x02C869F27B0D09004107818B1150e354d38Cb189#writeContract), if you're using browser-syncable wallet like metamask, or by interacting with contract by any convenient tool of your choice). They are not divisible, so every transaction uses 1 or more tokens, and you mint 1 at a time. Mint as many as you need.
* Then, deposit these tokens to Mumbai testnet. You can use the following script to do so:

```python
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
```

You can wait for these tokens to be added with `pos_client.is_deposited(transaction_hash)` or just monitor your balance with your wallet or an explorer.

If you've spent all of the tokens, you can mint a couple more.

## ERC1155

We use "Test ERC1155 (DERC1155)" as a ERC1155 token example.

Mapped contracts:
- parent: [0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063](https://goerli.etherscan.io/address/0x2e3Ef7931F2d0e4a7da3dea950FF3F19269d9063)
- child: [0xA07e45A987F19E25176c877d98388878622623FA](https://mumbai.polygonscan.com/address/0xA07e45A987F19E25176c877d98388878622623FA)

You can obtain tokens on both testnets via the [polygon faucet](https://faucet.polygon.technology/).


# Troubleshooting

If you feel like something is going wrong with RPC, try waiting first. Although JS SDK claims to provide low timeouts, sometimes checkpoint event takes 2 hours to complete (see CI tests run time - it's waiting for 3 checkpoint events), StateSync - up to 20 minutes. If transactions are lost or pending for a long time, try sending zero MATIC to your address - sometimes it resolves this issue.
