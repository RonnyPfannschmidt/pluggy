"""
Hook implementation classes.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Final
from typing import final

from ._config import HookimplConfiguration
from ._decorators import varnames


_Plugin = object
_HookImplFunction = Callable[..., Any]


class HookImpl:
    """A hook implementation in a :class:`HookCaller`."""

    __slots__ = (
        "function",
        "argnames",
        "kwargnames",
        "plugin",
        "opts",
        "plugin_name",
        "wrapper",
        "hookwrapper",
        "optionalhook",
        "tryfirst",
        "trylast",
    )

    def __init__(
        self,
        plugin: _Plugin,
        plugin_name: str,
        function: _HookImplFunction,
        hook_impl_opts: HookimplConfiguration,
    ) -> None:
        """:meta private:"""
        #: The hook implementation function.
        self.function: Final = function
        argnames, kwargnames = varnames(self.function)
        #: The positional parameter names of ``function```.
        self.argnames: Final = argnames
        #: The keyword parameter names of ``function```.
        self.kwargnames: Final = kwargnames
        #: The plugin which defined this hook implementation.
        self.plugin: Final = plugin
        #: The HookimplConfiguration used to configure this hook implementation.
        self.opts: Final = hook_impl_opts
        #: The name of the plugin which defined this hook implementation.
        self.plugin_name: Final = plugin_name
        #: Whether the hook implementation is a :ref:`wrapper <hookwrapper>`.
        self.wrapper: Final = hook_impl_opts.wrapper
        #: Whether the hook implementation is an :ref:`old-style wrapper
        #: <old_style_hookwrappers>`.
        self.hookwrapper: Final = hook_impl_opts.hookwrapper
        #: Whether validation against a hook specification is :ref:`optional
        #: <optionalhook>`.
        self.optionalhook: Final = hook_impl_opts.optionalhook
        #: Whether to try to order this hook implementation :ref:`first
        #: <callorder>`.
        self.tryfirst: Final = hook_impl_opts.tryfirst
        #: Whether to try to order this hook implementation :ref:`last
        #: <callorder>`.
        self.trylast: Final = hook_impl_opts.trylast

    def __repr__(self) -> str:
        return f"<HookImpl plugin_name={self.plugin_name!r}, plugin={self.plugin!r}>"


@final
class NormalImpl(HookImpl):
    """A normal (non-wrapper) hook implementation."""

    def __init__(
        self,
        plugin: _Plugin,
        plugin_name: str,
        function: _HookImplFunction,
        hook_impl_opts: HookimplConfiguration,
    ) -> None:
        assert not hook_impl_opts.wrapper and not hook_impl_opts.hookwrapper
        super().__init__(plugin, plugin_name, function, hook_impl_opts)


@final
class WrapperImpl(HookImpl):
    """A wrapper hook implementation."""

    def __init__(
        self,
        plugin: _Plugin,
        plugin_name: str,
        function: _HookImplFunction,
        hook_impl_opts: HookimplConfiguration,
    ) -> None:
        assert hook_impl_opts.wrapper or hook_impl_opts.hookwrapper
        super().__init__(plugin, plugin_name, function, hook_impl_opts)
