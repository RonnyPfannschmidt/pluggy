"""
Call loop machinery - compatibility re-export module.
"""

from __future__ import annotations

# Import _multicall from the execution module
from ._execution import _multicall


# Re-export for compatibility
__all__ = ["_multicall"]
