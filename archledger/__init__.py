from __future__ import annotations

try:
    from archledger._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["__version__"]
