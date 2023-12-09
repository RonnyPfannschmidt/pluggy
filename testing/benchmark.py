"""
Benchmarking and performance tests.
"""
import types
from typing import Generator
from typing import Protocol


import pytest

from pluggy import HookimplMarker
from pluggy import HookRelay
from pluggy import HookspecMarker
from pluggy import PluginManager
from pluggy._callers import _multicall
from pluggy._hooks import HookImpl


class BenchmarkProtocol(Protocol):
    "stand in for missing types in pytest-benchmark"

    def __call__(self, object, *k: object, **kw: object) -> None:
        pass

    def pedantic(self, object, *k: object, **kw: object) -> None:
        pass


hookspec = HookspecMarker("example")
hookimpl = HookimplMarker("example")


@hookimpl
def hook(arg1, arg2, arg3):
    return arg1, arg2, arg3


@hookimpl(wrapper=True)
def wrapper(arg1: object, arg2: object, arg3: object) -> Generator[None, None, None]:
    return (yield)


@pytest.fixture(params=[10, 100], ids="hooks={}".format)
def hooks(request: pytest.FixtureRequest) -> list[types.FunctionType]:
    return [hook] * request.param


@pytest.fixture(params=[10, 100], ids="wrappers={}".format)
def wrappers(request: pytest.FixtureRequest) -> list[types.FunctionType]:
    return [wrapper] * request.param


def test_hook_and_wrappers_speed(
    benchmark: BenchmarkProtocol,
    hooks: list[types.FunctionType],
    wrappers: list[types.FunctionType],
) -> None:
    def setup() -> tuple[tuple[object, ...], dict[str, object]]:
        hook_name = "foo"
        hook_impls = []
        for method in hooks + wrappers:
            f = HookImpl(None, "<temp>", method, method.example_impl)
            hook_impls.append(f)
        caller_kwargs = {"arg1": 1, "arg2": 2, "arg3": 3}
        firstresult = False
        return (hook_name, hook_impls, caller_kwargs, firstresult), {}

    benchmark.pedantic(_multicall, setup=setup, rounds=10)


@pytest.mark.parametrize(
    ("plugins, wrappers, nesting"),
    [
        (1, 1, 0),
        (1, 1, 1),
        (1, 1, 5),
        (1, 5, 1),
        (1, 5, 5),
        (5, 1, 1),
        (5, 1, 5),
        (5, 5, 1),
        (5, 5, 5),
        (20, 20, 0),
        (100, 100, 0),
    ],
)
def test_call_hook(
    benchmark: BenchmarkProtocol, plugins: int, wrappers: int, nesting: int
) -> None:
    pm = PluginManager("example")

    class HookSpec:
        @hookspec
        def fun(self, hooks: HookRelay, nesting: int) -> None:
            pass

    class Plugin:
        def __init__(self, num: int) -> None:
            self.num = num

        def __repr__(self) -> str:
            return f"<Plugin {self.num}>"

        @hookimpl
        def fun(self, hooks: HookRelay, nesting: int) -> None:
            if nesting:
                hooks.fun(hooks=hooks, nesting=nesting - 1)

    class PluginWrap:
        def __init__(self, num: int) -> None:
            self.num = num

        def __repr__(self) -> str:
            return f"<PluginWrap {self.num}>"

        @hookimpl(wrapper=True)
        def fun(self) -> Generator[None, None, None]:
            return (yield)

    pm.add_hookspecs(HookSpec)

    for i in range(plugins):
        pm.register(Plugin(i), name=f"plug_{i}")
    for i in range(wrappers):
        pm.register(PluginWrap(i), name=f"wrap_plug_{i}")

    benchmark(pm.hook.fun, hooks=pm.hook, nesting=nesting)
