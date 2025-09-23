"""
Hook caller classes.
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from collections.abc import Set
from types import ModuleType
from typing import Any
from typing import Final
from typing import final
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union
import warnings

from ._config import HookimplConfiguration
from ._config import HookspecConfiguration
from ._decorators import HookSpec
from ._implementation import HookImpl


_Namespace = Union[ModuleType, type]
_Plugin = object
_HookExec = Callable[
    [str, Sequence[HookImpl], Mapping[str, object], bool],
    Union[object, list[object]],
]
_CallHistory = list[tuple[Mapping[str, object], Optional[Callable[[Any], None]]]]


def _insert_hookimpl_into_list(
    hookimpls: list[HookImpl],
    hookimpl: HookImpl,
    is_wrapper: bool,
) -> None:
    """Insert a hook implementation into the appropriate position in a list.

    The list is organized as:
    1. trylast nonwrappers
    2. nonwrappers
    3. tryfirst nonwrappers
    4. trylast wrappers
    5. wrappers
    6. tryfirst wrappers
    """
    # Find the split point between non-wrappers and wrappers
    for i, method in enumerate(hookimpls):
        if method.hookwrapper or method.wrapper:
            splitpoint = i
            break
    else:
        splitpoint = len(hookimpls)

    if is_wrapper:
        start, end = splitpoint, len(hookimpls)
    else:
        start, end = 0, splitpoint

    if hookimpl.trylast:
        hookimpls.insert(start, hookimpl)
    elif hookimpl.tryfirst:
        hookimpls.insert(end, hookimpl)
    else:
        # find last non-tryfirst method
        i = end - 1
        while i >= start and hookimpls[i].tryfirst:
            i -= 1
        hookimpls.insert(i + 1, hookimpl)


class HookCaller:
    """A caller of all registered implementations of a hook specification."""

    __slots__ = (
        "name",
        "spec",
        "_hookexec",
        "_normal_hookimpls",
        "_wrapper_hookimpls",
        "_call_history",
    )

    name: Final[str]
    spec: HookSpec | None
    _hookexec: Final[_HookExec]
    _normal_hookimpls: Final[list[HookImpl]]
    _wrapper_hookimpls: Final[list[HookImpl]]
    _call_history: _CallHistory | None

    def __init__(
        self,
        name: str,
        hook_execute: _HookExec,
        specmodule_or_class: _Namespace | None = None,
        spec_opts: HookspecConfiguration | None = None,
    ) -> None:
        """:meta private:"""
        #: Name of the hook getting called.
        self.name = name
        self._hookexec = hook_execute
        # Separate lists for normal and wrapper implementations
        # Normal impls: trylast -> normal -> tryfirst
        # Wrapper impls: trylast -> normal -> tryfirst
        self._normal_hookimpls = []
        self._wrapper_hookimpls = []
        self._call_history: _CallHistory | None = None
        # TODO: Document, or make private.
        self.spec: HookSpec | None = None
        if specmodule_or_class is not None:
            assert spec_opts is not None
            self.set_specification(specmodule_or_class, spec_opts)

    # TODO: Document, or make private.
    def has_spec(self) -> bool:
        return self.spec is not None

    # TODO: Document, or make private.
    def set_specification(
        self,
        specmodule_or_class: _Namespace,
        spec_opts: HookspecConfiguration,
    ) -> None:
        if self.spec is not None:
            raise ValueError(
                f"Hook {self.spec.name!r} is already registered "
                f"within namespace {self.spec.namespace}"
            )
        self.spec = HookSpec(specmodule_or_class, self.name, spec_opts)
        if spec_opts.historic:
            self._call_history = []

    def is_historic(self) -> bool:
        """Whether this caller is :ref:`historic <historic>`."""
        return self._call_history is not None

    def _remove_plugin(self, plugin: _Plugin) -> None:
        # Try to remove from normal implementations
        for i, method in enumerate(self._normal_hookimpls):
            if method.plugin == plugin:
                del self._normal_hookimpls[i]
                return
        # Try to remove from wrapper implementations
        for i, method in enumerate(self._wrapper_hookimpls):
            if method.plugin == plugin:
                del self._wrapper_hookimpls[i]
                return
        raise ValueError(f"plugin {plugin!r} not found")

    def get_hookimpls(self) -> list[HookImpl]:
        """Get all registered hook implementations for this hook."""
        # Return combined list: normal implementations followed by wrappers
        return self._normal_hookimpls.copy() + self._wrapper_hookimpls.copy()

    def _add_hookimpl(self, hookimpl: HookImpl) -> None:
        """Add an implementation to the callback chain."""
        is_wrapper = hookimpl.hookwrapper or hookimpl.wrapper
        target_list = self._wrapper_hookimpls if is_wrapper else self._normal_hookimpls

        # Insert in correct position based on tryfirst/trylast
        if hookimpl.trylast:
            target_list.insert(0, hookimpl)
        elif hookimpl.tryfirst:
            target_list.append(hookimpl)
        else:
            # Find last non-tryfirst method
            i = len(target_list) - 1
            while i >= 0 and target_list[i].tryfirst:
                i -= 1
            target_list.insert(i + 1, hookimpl)

    def __repr__(self) -> str:
        return f"<HookCaller {self.name!r}>"

    def _verify_all_args_are_provided(self, kwargs: Mapping[str, object]) -> None:
        # This is written to avoid expensive operations when not needed.
        if self.spec:
            for argname in self.spec.argnames:
                if argname not in kwargs:
                    notincall = ", ".join(
                        repr(argname)
                        for argname in self.spec.argnames
                        # Avoid self.spec.argnames - kwargs.keys()
                        # it doesn't preserve order.
                        if argname not in kwargs.keys()
                    )
                    warnings.warn(
                        f"Argument(s) {notincall} which are declared in the hookspec "
                        "cannot be found in this hook call",
                        stacklevel=2,
                    )
                    break

    def __call__(self, **kwargs: object) -> Any:
        """Call the hook.

        Only accepts keyword arguments, which should match the hook
        specification.

        Returns the result(s) of calling all registered plugins, see
        :ref:`calling`.
        """
        assert not self.is_historic(), (
            "Cannot directly call a historic hook - use call_historic instead."
        )
        self._verify_all_args_are_provided(kwargs)
        firstresult = self.spec.opts.firstresult if self.spec else False
        # Copy because plugins may register other plugins during iteration (#438).
        # Combine normal and wrapper implementations
        hookimpls = self._normal_hookimpls.copy() + self._wrapper_hookimpls.copy()
        return self._hookexec(self.name, hookimpls, kwargs, firstresult)

    def call_historic(
        self,
        result_callback: Callable[[Any], None] | None = None,
        kwargs: Mapping[str, object] | None = None,
    ) -> None:
        """Call the hook with given ``kwargs`` for all registered plugins and
        for all plugins which will be registered afterwards, see
        :ref:`historic`.

        :param result_callback:
            If provided, will be called for each non-``None`` result obtained
            from a hook implementation.
        """
        assert self._call_history is not None
        kwargs = kwargs or {}
        self._verify_all_args_are_provided(kwargs)
        self._call_history.append((kwargs, result_callback))
        # Historizing hooks don't return results.
        # Remember firstresult isn't compatible with historic.
        # Copy because plugins may register other plugins during iteration (#438).
        # Combine normal and wrapper implementations
        hookimpls = self._normal_hookimpls.copy() + self._wrapper_hookimpls.copy()
        res = self._hookexec(self.name, hookimpls, kwargs, False)
        if result_callback is None:
            return
        if isinstance(res, list):
            for x in res:
                result_callback(x)

    def call_extra(
        self, methods: Sequence[Callable[..., object]], kwargs: Mapping[str, object]
    ) -> Any:
        """Call the hook with some additional temporarily participating
        methods using the specified ``kwargs`` as call parameters, see
        :ref:`call_extra`."""
        assert not self.is_historic(), (
            "Cannot directly call a historic hook - use call_historic instead."
        )
        self._verify_all_args_are_provided(kwargs)
        opts = HookimplConfiguration(
            wrapper=False,
            hookwrapper=False,
            optionalhook=False,
            trylast=False,
            tryfirst=False,
            specname=None,
        )
        # Create a combined list for call_extra
        normal_impls = self._normal_hookimpls.copy()
        wrapper_impls = self._wrapper_hookimpls.copy()

        for method in methods:
            hookimpl = HookImpl(None, "<temp>", method, opts)
            # Add to normal implementations (since opts has wrapper=False)
            # Find last non-tryfirst method
            i = len(normal_impls) - 1
            while i >= 0 and normal_impls[i].tryfirst:
                i -= 1
            normal_impls.insert(i + 1, hookimpl)

        hookimpls = normal_impls + wrapper_impls
        firstresult = self.spec.opts.firstresult if self.spec else False
        return self._hookexec(self.name, hookimpls, kwargs, firstresult)

    def _maybe_apply_history(self, method: HookImpl) -> None:
        """Apply call history to a new hookimpl if it is marked as historic."""
        if self.is_historic():
            assert self._call_history is not None
            for kwargs, result_callback in self._call_history:
                res = self._hookexec(self.name, [method], kwargs, False)
                if res and result_callback is not None:
                    # XXX: remember firstresult isn't compat with historic
                    assert isinstance(res, list)
                    result_callback(res[0])


class NormalHookCaller(HookCaller):
    """A hook caller for normal (non-historic) hooks."""

    def __init__(
        self,
        name: str,
        hook_execute: _HookExec,
        specmodule_or_class: _Namespace | None = None,
        spec_opts: HookspecConfiguration | None = None,
    ) -> None:
        if spec_opts is not None and spec_opts.historic:
            raise ValueError(f"Hook {name!r} is historic, use HistoricHookCaller")
        super().__init__(name, hook_execute, specmodule_or_class, spec_opts)


class HistoricHookCaller(HookCaller):
    """A hook caller for historic hooks.

    Historic hooks remember all calls and replay them for newly registered plugins.
    They don't support wrappers.
    """

    def __init__(
        self,
        name: str,
        hook_execute: _HookExec,
        specmodule_or_class: _Namespace | None = None,
        spec_opts: HookspecConfiguration | None = None,
    ) -> None:
        if spec_opts is not None:
            if not spec_opts.historic:
                raise ValueError(f"Hook {name!r} is not historic, use NormalHookCaller")
            if spec_opts.firstresult:
                raise ValueError("cannot have a historic firstresult hook")
        super().__init__(name, hook_execute, specmodule_or_class, spec_opts)

    def _add_hookimpl(self, hookimpl: HookImpl) -> None:
        """Add an implementation to the callback chain.

        Historic hooks don't support wrappers.
        """
        if hookimpl.hookwrapper or hookimpl.wrapper:
            raise ValueError(
                f"Plugin {hookimpl.plugin_name!r}\n"
                f"hook {self.name!r}\n"
                "historic incompatible with yield/wrapper/hookwrapper"
            )
        super()._add_hookimpl(hookimpl)


# Historical name (pluggy<=1.2), kept for backward compatibility.
_HookCaller = HookCaller


@final
class HookRelay:
    """Hook holder object for performing 1:N hook calls where N is the number
    of registered plugins."""

    __slots__ = ("__dict__",)

    def __init__(self) -> None:
        """:meta private:"""

    if TYPE_CHECKING:

        def __getattr__(self, name: str) -> HookCaller: ...


# Historical name (pluggy<=1.2), kept for backward compatibility.
_HookRelay = HookRelay


class _SubsetHookCaller(HookCaller):
    """A proxy to another HookCaller which manages calls to all registered
    plugins except the ones from remove_plugins."""

    # This class is unusual: in inhertits from `HookCaller` so all of
    # the *code* runs in the class, but it delegates all underlying *data*
    # to the original HookCaller.
    # `subset_hook_caller` used to be implemented by creating a full-fledged
    # HookCaller, copying all hookimpls from the original. This had problems
    # with memory leaks (#346) and historic calls (#347), which make a proxy
    # approach better.
    # An alternative implementation is to use a `_getattr__`/`__getattribute__`
    # proxy, however that adds more overhead and is more tricky to implement.

    __slots__ = (
        "_orig",
        "_remove_plugins",
    )

    def __init__(self, orig: HookCaller, remove_plugins: Set[_Plugin]) -> None:
        self._orig = orig
        self._remove_plugins = remove_plugins
        self.name = orig.name  # type: ignore[misc]
        self._hookexec = orig._hookexec  # type: ignore[misc]

    @property  # type: ignore[misc]
    def _normal_hookimpls(self) -> list[HookImpl]:
        return [
            impl
            for impl in self._orig._normal_hookimpls
            if impl.plugin not in self._remove_plugins
        ]

    @property  # type: ignore[misc]
    def _wrapper_hookimpls(self) -> list[HookImpl]:
        return [
            impl
            for impl in self._orig._wrapper_hookimpls
            if impl.plugin not in self._remove_plugins
        ]

    @property
    def spec(self) -> HookSpec | None:  # type: ignore[override]
        return self._orig.spec

    @property
    def _call_history(self) -> _CallHistory | None:  # type: ignore[override]
        return self._orig._call_history

    def __repr__(self) -> str:
        return f"<_SubsetHookCaller {self.name!r}>"
