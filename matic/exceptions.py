from __future__ import annotations


class MaticException(Exception):
    pass


class AllowedOnRootException(MaticException):
    """The action is allowed only on root token."""


class AllowedOnChildException(MaticException):
    """The action is allowed only on child token."""


class UnknownException(MaticException):
    """Unknown exception."""

    # FIXME: remove this idiotic ex


class ProofAPINotSetException(MaticException):
    """Proof api is not set, please set it using 'setProofApi'"""


class BurnTxNotCheckPointedException(MaticException):
    """Burn transaction has not been checkpointed as yet"""


class EIP1559NotSupportedException(MaticException):
    """The chain doesn't support eip-1559"""


class NullSpenderAddressException(MaticException):
    """Please provide spender address."""
