"""
Tests for ProjectSpec functionality.
"""

from pluggy import HookimplMarker
from pluggy import HookspecMarker
from pluggy import PluginManager
from pluggy._project import ProjectSpec


def test_project_spec_creation():
    """Test basic ProjectSpec creation and attributes."""
    spec = ProjectSpec("myproject")

    assert spec.project_name == "myproject"
    assert isinstance(spec.hookspec, HookspecMarker)
    assert isinstance(spec.hookimpl, HookimplMarker)
    assert spec.hookspec.project_name == "myproject"
    assert spec.hookimpl.project_name == "myproject"
    assert repr(spec) == "<ProjectSpec project_name='myproject'>"


def test_project_spec_create_plugin_manager():
    """Test creating a PluginManager from ProjectSpec."""
    spec = ProjectSpec("myproject")
    pm = spec.create_plugin_manager()

    assert isinstance(pm, PluginManager)
    assert pm.project_name == "myproject"
    assert pm._project_spec is None  # Default PluginManager doesn't store spec


def test_plugin_manager_accepts_project_spec():
    """Test that PluginManager accepts a ProjectSpec."""
    spec = ProjectSpec("myproject")
    pm = PluginManager(spec)

    assert pm.project_name == "myproject"
    assert pm._project_spec is spec


def test_plugin_manager_accepts_string():
    """Test that PluginManager still accepts a string project name."""
    pm = PluginManager("myproject")

    assert pm.project_name == "myproject"
    assert pm._project_spec is None


def test_project_spec_with_hooks():
    """Test ProjectSpec with actual hook usage."""
    spec = ProjectSpec("myproject")
    pm = spec.create_plugin_manager()

    class MySpec:
        @spec.hookspec
        def myhook(self, arg):
            pass

    class Plugin:
        @spec.hookimpl
        def myhook(self, arg):
            return arg * 2

    pm.add_hookspecs(MySpec)
    pm.register(Plugin())

    result = pm.hook.myhook(arg=5)
    assert result == [10]


def test_project_spec_config_helpers():
    """Test configuration helper methods."""
    spec = ProjectSpec("myproject")

    # Test hookspec config
    hookspec_config = spec.get_hookspec_config(firstresult=True, historic=False)
    assert hookspec_config.firstresult is True
    assert hookspec_config.historic is False

    # Test hookimpl config
    hookimpl_config = spec.get_hookimpl_config(
        wrapper=True, tryfirst=True, optionalhook=False
    )
    assert hookimpl_config.wrapper is True
    assert hookimpl_config.tryfirst is True
    assert hookimpl_config.optionalhook is False


def test_project_spec_custom_manager_class():
    """Test ProjectSpec with custom PluginManager class."""

    class CustomPluginManager(PluginManager):
        def custom_method(self) -> str:
            return "custom"

    spec = ProjectSpec("myproject", plugin_manager_cls=CustomPluginManager)
    pm = spec.create_plugin_manager()

    assert isinstance(pm, CustomPluginManager)
    assert pm.custom_method() == "custom"
    assert pm.project_name == "myproject"


def test_project_spec_shared_markers():
    """Test that markers from ProjectSpec are shared across components."""
    spec = ProjectSpec("myproject")

    # Use the same markers for multiple plugin managers
    pm1 = spec.create_plugin_manager()
    pm2 = spec.create_plugin_manager()

    class MySpec:
        @spec.hookspec
        def myhook(self):
            pass

    class Plugin1:
        @spec.hookimpl
        def myhook(self):
            return "plugin1"

    class Plugin2:
        @spec.hookimpl
        def myhook(self):
            return "plugin2"

    # Add specs to both managers
    pm1.add_hookspecs(MySpec)
    pm2.add_hookspecs(MySpec)

    # Register different plugins
    pm1.register(Plugin1())
    pm2.register(Plugin2())

    # Each manager has its own plugins
    assert pm1.hook.myhook() == ["plugin1"]
    assert pm2.hook.myhook() == ["plugin2"]
