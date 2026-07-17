"""Shared Archledger write guard using filelock.

All state-producing or mutating commands must acquire this lock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

from archledger.errors import ArchledgerError

_LOCK_FILENAME = "write.lock"
_LOCK_TIMEOUT = 0.1  # seconds — fail fast on contention


class WriteGuard:
    """Exclusive write lock for Archledger mutating operations.

    Lock file lives at ``.ledger/archledger/write.lock``, outside the
    movable ``data`` mount.
    """

    def __init__(self, project_root: Path) -> None:
        self._lock_dir = project_root / ".ledger" / "archledger"
        self._lock_path = self._lock_dir / _LOCK_FILENAME
        self._lock: FileLock | None = None

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    def acquire(self) -> None:
        """Acquire the exclusive write lock.

        Raises ArchledgerError with code ARCHLEDGER_WRITE_LOCK_HELD on
        contention.
        """
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        lock = FileLock(str(self._lock_path), timeout=_LOCK_TIMEOUT)
        try:
            lock.acquire()
        except Timeout:
            raise ArchledgerError(
                f"Another Archledger writer holds the lock: {self._lock_path}",
                details={
                    "code": "ARCHLEDGER_WRITE_LOCK_HELD",
                    "lock_path": str(self._lock_path),
                },
            ) from None
        self._lock = lock

    def release(self) -> None:
        """Release the write lock."""
        if self._lock is not None:
            self._lock.release()
            self._lock = None

    def __enter__(self) -> WriteGuard:
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()


def acquire_write_guard(project_root: Path) -> WriteGuard:
    """Acquire the Archledger write lock as a context manager.

    Usage::

        with acquire_write_guard(project_root) as guard:
            # mutating operations
    """
    guard = WriteGuard(project_root)
    guard.acquire()
    return guard


__all__ = ["WriteGuard", "acquire_write_guard"]
