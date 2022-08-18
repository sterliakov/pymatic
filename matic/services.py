from __future__ import annotations

from typing import Any

import requests

from matic.json_types import CheckpointedBlock
from matic.utils.polyfill import removeprefix, removesuffix

DEFAULT_ABI_STORE_URL: str = 'https://static.matic.network/network'
"""Default url of ABI store. Can be altered if needed."""

DEFAULT_PROOF_API_URL: str = ''
"""Default url of proof API. Must be set to use fast proofs."""


def get_abi(
    network: str,
    version: str,
    bridge_type: str,
    contract_name: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Get ABI dict for contract."""
    base_url = removesuffix(base_url or DEFAULT_ABI_STORE_URL, '/')
    url = f'{base_url}/{network}/{version}/artifacts/{bridge_type}/{contract_name}.json'
    return requests.get(url).json()['abi']


def get_address(
    network: str, version: str, base_url: str | None = None
) -> dict[str, Any]:
    """Fetch dictionary with addresses of contracts deployed on network."""
    base_url = removesuffix(base_url or DEFAULT_ABI_STORE_URL, '/')
    url = f'{base_url}/{network}/{version}/index.json'
    return requests.get(url).json()


def _create_proof_url(network: str, url: str, base_url: str | None = None) -> str:
    base_url = removesuffix(base_url or DEFAULT_PROOF_API_URL, '/')
    if not base_url:
        raise RuntimeError('Please set DEFAULT_PROOF_API_URL or pass base_url.')
    url = removeprefix(url, '/')
    return f'{base_url}/{"matic" if network == "mainnet" else "mumbai"}/{url}'


def get_block_included(
    network: str, block_number: int, base_url: str | None = None
) -> CheckpointedBlock:
    """Get block information by number."""
    url = _create_proof_url(network, f'/block-included/{block_number}')
    data = requests.get(url).json()
    return CheckpointedBlock(
        header_block_number=int(data['headerBlockNumber'], 16),
        block_number=int(data['blockNumber']),
        start=int(data['start']),
        end=int(data['end']),
        proposer=data['proposer'],
        root=data['root'],
        created_at=int(data['createdAt']),
        message=data['message'],
    )


def get_proof(
    network: str, start: int, end: int, block_number: int, base_url: str | None = None
) -> bytes:
    """Get proof from API."""
    url = _create_proof_url(
        network,
        f'/fast-merkle-proof?start={start}&end={end}&number={block_number}',
    )
    return bytes.fromhex(removeprefix(requests.get(url).json()['proof'], '0x'))
