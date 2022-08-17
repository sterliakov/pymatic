from __future__ import annotations

from typing import Any

import requests

DEFAULT_ABI_STORE_URL: str = 'https://static.matic.network/network'
"""Default url of ABI store. Can be altered if needed."""

DEFAULT_PROOF_API_URL: str = ''
"""Default url of ABI store. Can be altered if needed."""


def get_abi(
    network: str,
    version: str,
    bridge_type: str,
    contract_name: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    base_url = (base_url or DEFAULT_ABI_STORE_URL).removesuffix('/')
    url = f'{base_url}/{network}/{version}/artifacts/{bridge_type}/{contract_name}.json'
    return requests.get(url).json()['abi']


def get_address(
    network: str, version: str, base_url: str | None = None
) -> dict[str, Any]:
    base_url = (base_url or DEFAULT_ABI_STORE_URL).removesuffix('/')
    url = f'{base_url}/{network}/{version}/index.json'
    return requests.get(url).json()


def _create_proof_url(network: str, url: str, base_url: str | None = None):
    base_url = (base_url or DEFAULT_PROOF_API_URL).removesuffix('/')
    if not base_url:
        raise RuntimeError('Please set DEFAULT_PROOF_API_URL or pass base_url.')
    url = url.removeprefix('/')
    return f'{base_url}/{"matic" if network == "mainnet" else "mumbai"}/{url}'


def get_block_included(network: str, block_number: int, base_url: str | None = None):
    url = _create_proof_url(network, f'/block-included/{block_number}')
    return requests.get(url).json()
    # FIXME: need to cast?


def get_proof(network: str, start, end, block_number, base_url: str | None = None):
    url = _create_proof_url(
        network,
        f'/fast-merkle-proof?start={start}&end={end}&number={block_number}',
    )
    return requests.get(url).json()['proof']
