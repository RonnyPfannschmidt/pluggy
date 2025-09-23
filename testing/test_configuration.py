"""
Tests for configuration classes.
"""

import pytest

from pluggy import HookimplConfiguration
from pluggy import HookspecConfiguration


class TestHookspecConfiguration:
    def test_basic_creation(self):
        config = HookspecConfiguration()
        assert config.firstresult is False
        assert config.historic is False
        assert config.warn_on_impl is None
        assert config.warn_on_impl_args is None

    def test_firstresult(self):
        config = HookspecConfiguration(firstresult=True)
        assert config.firstresult is True
        assert config.historic is False

    def test_historic(self):
        config = HookspecConfiguration(historic=True)
        assert config.firstresult is False
        assert config.historic is True

    def test_historic_firstresult_validation(self):
        with pytest.raises(ValueError, match="cannot have a historic firstresult"):
            HookspecConfiguration(historic=True, firstresult=True)

    def test_warn_on_impl(self):
        warning = UserWarning("test warning")
        config = HookspecConfiguration(warn_on_impl=warning)
        assert config.warn_on_impl is warning

    def test_warn_on_impl_args(self):
        warnings_dict = {"arg1": UserWarning("arg1 warning")}
        config = HookspecConfiguration(warn_on_impl_args=warnings_dict)
        assert config.warn_on_impl_args is warnings_dict


class TestHookimplConfiguration:
    def test_basic_creation(self):
        config = HookimplConfiguration()
        assert config.wrapper is False
        assert config.hookwrapper is False
        assert config.optionalhook is False
        assert config.tryfirst is False
        assert config.trylast is False
        assert config.specname is None

    def test_wrapper(self):
        config = HookimplConfiguration(wrapper=True)
        assert config.wrapper is True
        assert config.hookwrapper is False

    def test_hookwrapper(self):
        config = HookimplConfiguration(hookwrapper=True)
        assert config.wrapper is False
        assert config.hookwrapper is True

    def test_both_wrappers_allowed(self):
        """Both wrapper types are allowed at config level, validation happens later."""
        config = HookimplConfiguration(wrapper=True, hookwrapper=True)
        assert config.wrapper is True
        assert config.hookwrapper is True

    def test_tryfirst(self):
        config = HookimplConfiguration(tryfirst=True)
        assert config.tryfirst is True
        assert config.trylast is False

    def test_trylast(self):
        config = HookimplConfiguration(trylast=True)
        assert config.tryfirst is False
        assert config.trylast is True

    def test_optionalhook(self):
        config = HookimplConfiguration(optionalhook=True)
        assert config.optionalhook is True

    def test_specname(self):
        config = HookimplConfiguration(specname="custom_name")
        assert config.specname == "custom_name"


def test_config_integration_with_hooks():
    """Test that configurations work correctly with actual hooks."""
    from pluggy import HookimplMarker
    from pluggy import HookspecMarker
    from pluggy import PluginManager

    pm = PluginManager("test")
    hookspec = HookspecMarker("test")
    hookimpl = HookimplMarker("test")

    # Use firstresult hookspec
    class MySpec:
        @hookspec(firstresult=True)
        def myhook(self, arg):
            pass

    # Multiple implementations
    class Plugin1:
        @hookimpl(trylast=True)
        def myhook(self, arg):
            return f"plugin1: {arg}"

    class Plugin2:
        @hookimpl(tryfirst=True)
        def myhook(self, arg):
            return f"plugin2: {arg}"

    pm.add_hookspecs(MySpec)
    pm.register(Plugin1())
    pm.register(Plugin2())

    # With firstresult, should get plugin2's result (tryfirst)
    result = pm.hook.myhook(arg="test")
    assert result == "plugin2: test"


def test_historic_hook_configuration():
    """Test historic hook configuration."""
    from pluggy import HookimplMarker
    from pluggy import HookspecMarker
    from pluggy import PluginManager

    pm = PluginManager("test")
    hookspec = HookspecMarker("test")
    hookimpl = HookimplMarker("test")

    results: list[str] = []

    class MySpec:
        @hookspec(historic=True)
        def myhook(self, arg):
            pass

    pm.add_hookspecs(MySpec)

    # Call hook before any plugin registered
    pm.hook.myhook.call_historic(
        kwargs={"arg": "call1"}, result_callback=results.append
    )

    class Plugin1:
        @hookimpl
        def myhook(self, arg):
            return f"plugin1: {arg}"

    # Register plugin - should replay historic call
    pm.register(Plugin1())

    # Check that historic call was replayed
    assert "plugin1: call1" in results
