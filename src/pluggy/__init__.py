__all__ = [
    "__version__",
    "PluginManager",
    "PluginValidationError",
    "HookCaller",
    "NormalHookCaller",
    "HistoricHookCaller",
    "HookCallError",
    "HookspecOpts",
    "HookimplOpts",
    "HookspecConfiguration",
    "HookimplConfiguration",
    "HookImpl",
    "HookRelay",
    "HookspecMarker",
    "HookimplMarker",
    "Result",
    "PluggyWarning",
    "PluggyTeardownRaisedWarning",
    "ProjectSpec",
]
from ._caller import HistoricHookCaller
from ._caller import HookCaller
from ._caller import NormalHookCaller
from ._config import HookimplConfiguration
from ._config import HookimplOpts
from ._config import HookspecConfiguration
from ._config import HookspecOpts
from ._decorators import HookimplMarker
from ._decorators import HookspecMarker
from ._hooks import HookImpl
from ._hooks import HookRelay
from ._manager import PluginManager
from ._manager import PluginValidationError
from ._project import ProjectSpec
from ._result import HookCallError
from ._result import Result
from ._warnings import PluggyTeardownRaisedWarning
from ._warnings import PluggyWarning


def __getattr__(name: str) -> str:
    if name == "__version__":
        from importlib.metadata import version

        return version("pluggy")

    raise AttributeError(f"module {__name__} has no attribute {name!r}")
