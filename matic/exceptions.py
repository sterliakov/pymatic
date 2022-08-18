from __future__ import annotations


class MaticException(Exception):
    """Base exception class for this library."""


class AllowedOnRootException(MaticException):
    """The action is allowed only on root token."""


class AllowedOnChildException(MaticException):
    """The action is allowed only on child token."""


class ProofAPINotSetException(MaticException):
    """Proof api is not set."""


class BurnTxNotCheckPointedException(MaticException):
    """Burn transaction has not been checkpointed as yet."""


class EIP1559NotSupportedException(MaticException):
    """The chain doesn't support EIP-1559."""


class NullSpenderAddressException(MaticException):
    """Please provide spender address."""
