"""
Internal hook annotation, representation and calling machinery.

This module now serves as a compatibility layer, re-exporting symbols
from the reorganized modules.
"""

from __future__ import annotations

# Import types for annotations
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import Sequence
from types import ModuleType
from typing import TypeVar
from typing import Union

from ._caller import _HookCaller
from ._caller import _HookRelay
from ._caller import _SubsetHookCaller

# Re-export hook caller classes
from ._caller import HookCaller
from ._caller import HookRelay
from ._config import HookimplOpts

# Re-export configuration types
from ._config import HookspecOpts
from ._config import normalize_hookimpl_opts
from ._decorators import HookimplMarker
from ._decorators import HookSpec

# Re-export decorators and related
from ._decorators import HookspecMarker
from ._decorators import varnames

# Re-export implementation classes
from ._implementation import HookImpl


# Re-export type aliases
_T = TypeVar("_T")
_HookImplFunction = Callable[..., Union[_T, Generator[None, object, None]]]
_Namespace = Union[ModuleType, type]
_Plugin = object
_HookExec = Callable[
    [str, Sequence["HookImpl"], Mapping[str, object], bool],
    Union[object, list[object]],
]

__all__ = [
    "HookspecOpts",
    "HookimplOpts",
    "normalize_hookimpl_opts",
    "HookspecMarker",
    "HookimplMarker",
    "HookSpec",
    "varnames",
    "HookCaller",
    "HookRelay",
    "_HookCaller",
    "_HookRelay",
    "_SubsetHookCaller",
    "HookImpl",
    "_HookImplFunction",
    "_Namespace",
    "_Plugin",
    "_HookExec",
]
