"""
Tests for async support functionality.
"""

import pytest

from pluggy import HookimplMarker
from pluggy import HookspecMarker
from pluggy import PluginManager


def test_async_require_greenlet_import():
    """Test that Submitter requires greenlet to be available."""
    try:
        import greenlet  # noqa: F401
    except ImportError:
        pytest.skip("greenlet not available")

    from pluggy._async import Submitter

    # Should be able to create submitter
    submitter = Submitter()
    assert submitter._active_submitter is None
    assert "active=False" in repr(submitter)


def test_require_await_outside_context():
    """Test that require_await fails outside async context."""
    try:
        import greenlet  # noqa: F401
    except ImportError:
        pytest.skip("greenlet not available")

    from pluggy._async import Submitter

    submitter = Submitter()

    async def dummy_coro() -> int:
        return 42

    with pytest.raises(RuntimeError, match="outside of async context"):
        submitter.require_await(dummy_coro())


def test_basic_async_support():
    """Test basic async functionality."""
    try:
        import greenlet  # noqa: F401
    except ImportError:
        pytest.skip("greenlet not available")

    import asyncio

    pm = PluginManager("test")
    hookspec = HookspecMarker("test")
    hookimpl = HookimplMarker("test")

    class MySpec:
        @hookspec
        def myhook(self):
            pass

    class Plugin:
        @hookimpl
        def myhook(self):
            return "sync_result"

    pm.add_hookspecs(MySpec)
    pm.register(Plugin())

    # Normal sync call should work
    result = pm.hook.myhook()
    assert result == ["sync_result"]

    # Async context should also work for sync hooks
    async def test_async() -> None:
        async def run_hook():
            return pm.hook.myhook()

        result = await pm.run_async(run_hook)
        assert result == ["sync_result"]

    asyncio.run(test_async())


def test_awaitable_hook_result():
    """Test that hooks can return awaitables when in async context."""
    try:
        import greenlet  # noqa: F401
    except ImportError:
        pytest.skip("greenlet not available")

    import asyncio

    pm = PluginManager("test")
    hookspec = HookspecMarker("test")
    hookimpl = HookimplMarker("test")

    class MySpec:
        @hookspec
        def myhook(self):
            pass

    async def async_function() -> str:
        return "async_result"

    class Plugin:
        @hookimpl
        def myhook(self):
            # Return an awaitable
            return async_function()

    pm.add_hookspecs(MySpec)
    pm.register(Plugin())

    # Without async context, should return the awaitable
    result = pm.hook.myhook()
    assert len(result) == 1
    assert asyncio.iscoroutine(result[0])
    # Clean up the coroutine
    result[0].close()

    # With async context, should await the result
    async def test_async() -> None:
        async def run_hook():
            return pm.hook.myhook()

        result = await pm.run_async(run_hook)
        assert result == ["async_result"]

    asyncio.run(test_async())


def test_maybe_submit_without_context():
    """Test maybe_submit returns awaitable when not in context."""
    try:
        import greenlet  # noqa: F401
    except ImportError:
        pytest.skip("greenlet not available")

    from pluggy._async import Submitter

    submitter = Submitter()

    async def dummy_coro() -> int:
        return 42

    coro = dummy_coro()
    result = submitter.maybe_submit(coro)
    assert result is coro
    coro.close()  # Clean up
