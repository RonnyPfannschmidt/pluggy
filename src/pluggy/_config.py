"""
Configuration types and helpers for hook specifications and implementations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final
from typing import TypedDict


class HookspecOpts(TypedDict):
    """Options for a hook specification."""

    #: Whether the hook is :ref:`first result only <firstresult>`.
    firstresult: bool
    #: Whether the hook is :ref:`historic <historic>`.
    historic: bool
    #: Whether the hook :ref:`warns when implemented <warn_on_impl>`.
    warn_on_impl: Warning | None
    #: Whether the hook warns when :ref:`certain arguments are requested
    #: <warn_on_impl>`.
    #:
    #: .. versionadded:: 1.5
    warn_on_impl_args: Mapping[str, Warning] | None


class HookimplOpts(TypedDict):
    """Options for a hook implementation."""

    #: Whether the hook implementation is a :ref:`wrapper <hookwrapper>`.
    wrapper: bool
    #: Whether the hook implementation is an :ref:`old-style wrapper
    #: <old_style_hookwrappers>`.
    hookwrapper: bool
    #: Whether validation against a hook specification is :ref:`optional
    #: <optionalhook>`.
    optionalhook: bool
    #: Whether to try to order this hook implementation :ref:`first
    #: <callorder>`.
    tryfirst: bool
    #: Whether to try to order this hook implementation :ref:`last
    #: <callorder>`.
    trylast: bool
    #: The name of the hook specification to match, see :ref:`specname`.
    specname: str | None


class HookspecConfiguration:
    """Configuration for a hook specification.

    Replaces the legacy HookspecOpts TypedDict with proper validation.
    """

    __slots__ = (
        "firstresult",
        "historic",
        "warn_on_impl",
        "warn_on_impl_args",
    )

    firstresult: Final[bool]
    historic: Final[bool]
    warn_on_impl: Final[Warning | None]
    warn_on_impl_args: Final[Mapping[str, Warning] | None]

    def __init__(
        self,
        firstresult: bool = False,
        historic: bool = False,
        warn_on_impl: Warning | None = None,
        warn_on_impl_args: Mapping[str, Warning] | None = None,
    ) -> None:
        if historic and firstresult:
            raise ValueError("cannot have a historic firstresult hook")

        self.firstresult = firstresult
        self.historic = historic
        self.warn_on_impl = warn_on_impl
        self.warn_on_impl_args = warn_on_impl_args


class HookimplConfiguration:
    """Configuration for a hook implementation.

    Replaces the legacy HookimplOpts TypedDict with proper validation.
    """

    __slots__ = (
        "wrapper",
        "hookwrapper",
        "optionalhook",
        "tryfirst",
        "trylast",
        "specname",
    )

    wrapper: Final[bool]
    hookwrapper: Final[bool]
    optionalhook: Final[bool]
    tryfirst: Final[bool]
    trylast: Final[bool]
    specname: Final[str | None]

    def __init__(
        self,
        wrapper: bool = False,
        hookwrapper: bool = False,
        optionalhook: bool = False,
        tryfirst: bool = False,
        trylast: bool = False,
        specname: str | None = None,
    ) -> None:
        # Don't validate wrapper/hookwrapper - done during registration
        self.wrapper = wrapper
        self.hookwrapper = hookwrapper
        self.optionalhook = optionalhook
        self.tryfirst = tryfirst
        self.trylast = trylast
        self.specname = specname


def normalize_hookimpl_opts(opts: HookimplOpts) -> None:
    opts.setdefault("tryfirst", False)
    opts.setdefault("trylast", False)
    opts.setdefault("wrapper", False)
    opts.setdefault("hookwrapper", False)
    opts.setdefault("optionalhook", False)
    opts.setdefault("specname", None)


def hookspec_config_from_opts(opts: HookspecOpts) -> HookspecConfiguration:
    """Convert legacy HookspecOpts dict to HookspecConfiguration."""
    return HookspecConfiguration(
        firstresult=opts.get("firstresult", False),
        historic=opts.get("historic", False),
        warn_on_impl=opts.get("warn_on_impl"),
        warn_on_impl_args=opts.get("warn_on_impl_args"),
    )


def hookimpl_config_from_opts(opts: HookimplOpts) -> HookimplConfiguration:
    """Convert legacy HookimplOpts dict to HookimplConfiguration."""
    return HookimplConfiguration(
        wrapper=opts.get("wrapper", False),
        hookwrapper=opts.get("hookwrapper", False),
        optionalhook=opts.get("optionalhook", False),
        tryfirst=opts.get("tryfirst", False),
        trylast=opts.get("trylast", False),
        specname=opts.get("specname"),
    )
