from __future__ import annotations

import sys

if sys.version_info < (3, 9):

    def removeprefix(s: str, prefix: str, /) -> str:
        if s.startswith(prefix):
            return s[len(prefix) :]
        return s

    def removesuffix(s: str, suffix: str, /) -> str:
        if s.endswith(suffix):
            return s[: -len(suffix)]
        return s

else:
    removeprefix = str.removeprefix
    removesuffix = str.removesuffix
