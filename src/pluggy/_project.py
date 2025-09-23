"""
Project specification and configuration.
"""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from ._config import HookimplConfiguration
from ._config import HookspecConfiguration
from ._decorators import HookimplMarker
from ._decorators import HookspecMarker


if TYPE_CHECKING:
    from ._manager import PluginManager


class ProjectSpec:
    """Unified project configuration for pluggy.

    This class manages the project name and provides factory methods
    for creating consistent plugin managers and hook markers that all
    share the same project configuration.

    :param project_name: The short project name. Prefer snake case.
    :param plugin_manager_cls: Optional custom PluginManager class.
    """

    __slots__ = (
        "project_name",
        "_plugin_manager_cls",
        "_hookspec_marker",
        "_hookimpl_marker",
    )

    def __init__(
        self,
        project_name: str,
        plugin_manager_cls: type[PluginManager] | None = None,
    ) -> None:
        """Initialize ProjectSpec with project name and optional manager class."""
        self.project_name = project_name
        self._plugin_manager_cls = plugin_manager_cls

        # Create markers for this project
        self._hookspec_marker = HookspecMarker(project_name)
        self._hookimpl_marker = HookimplMarker(project_name)

    @property
    def hookspec(self) -> HookspecMarker:
        """Get the hook specification marker for this project."""
        return self._hookspec_marker

    @property
    def hookimpl(self) -> HookimplMarker:
        """Get the hook implementation marker for this project."""
        return self._hookimpl_marker

    def create_plugin_manager(self, **kwargs: Any) -> PluginManager:
        """Create a PluginManager instance for this project.

        :param kwargs: Additional arguments to pass to PluginManager constructor.
        :returns: A new PluginManager instance.
        """
        from ._manager import PluginManager

        manager_cls = self._plugin_manager_cls or PluginManager
        return manager_cls(self.project_name, **kwargs)

    def get_hookspec_config(
        self,
        firstresult: bool = False,
        historic: bool = False,
        warn_on_impl: Warning | None = None,
        warn_on_impl_args: dict[str, Warning] | None = None,
    ) -> HookspecConfiguration:
        """Create a hook specification configuration.

        This is a convenience method for creating HookspecConfiguration
        objects with this project's settings.

        :param firstresult: Whether to stop at first non-None result.
        :param historic: Whether this is a historic hook.
        :param warn_on_impl: Warning to issue when hook is implemented.
        :param warn_on_impl_args: Warnings for specific argument names.
        :returns: A new HookspecConfiguration instance.
        """
        return HookspecConfiguration(
            firstresult=firstresult,
            historic=historic,
            warn_on_impl=warn_on_impl,
            warn_on_impl_args=warn_on_impl_args,
        )

    def get_hookimpl_config(
        self,
        wrapper: bool = False,
        hookwrapper: bool = False,
        optionalhook: bool = False,
        tryfirst: bool = False,
        trylast: bool = False,
        specname: str | None = None,
    ) -> HookimplConfiguration:
        """Create a hook implementation configuration.

        This is a convenience method for creating HookimplConfiguration
        objects with this project's settings.

        :param wrapper: Whether this is a new-style wrapper.
        :param hookwrapper: Whether this is an old-style wrapper.
        :param optionalhook: Whether this hook is optional.
        :param tryfirst: Whether to try calling this hook first.
        :param trylast: Whether to try calling this hook last.
        :param specname: Alternative name for the hook specification.
        :returns: A new HookimplConfiguration instance.
        """
        return HookimplConfiguration(
            wrapper=wrapper,
            hookwrapper=hookwrapper,
            optionalhook=optionalhook,
            tryfirst=tryfirst,
            trylast=trylast,
            specname=specname,
        )

    def __repr__(self) -> str:
        return f"<ProjectSpec project_name={self.project_name!r}>"
