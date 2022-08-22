from logging import getLogger

from matic.pos import POSClient

__version__ = '0.1.0b2'

logger = getLogger(__name__)
"""Logger to use.

:meta hide-value:
"""


__all__ = ['POSClient', 'logger']
