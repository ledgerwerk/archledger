"""Archledger-owned round-trip TOML document API for tool config.

Uses tomlkit for comment-preserving, order-preserving reads and writes.
"""

from __future__ import annotations

from pathlib import Path

import tomlkit

from archledger.config.model import ProjectConfig
from archledger.config.parse import load_project_config
from archledger.errors import ConfigError


class ConfigDocument:
    """Mutable in-memory representation of an Archledger config file.

    Wraps a tomlkit document plus the parsed semantic model. Mutations
    update both the document and the model so that comments and
    formatting are preserved on write.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._raw = tomlkit.parse(path.read_text(encoding="utf-8"))
        if not isinstance(self._raw, tomlkit.TOMLDocument):
            raise ConfigError(
                f"Expected a TOML document, got {type(self._raw).__name__}"
            )
        self._model = load_project_config(path)

    @property
    def model(self) -> ProjectConfig:
        return self._model

    @property
    def path(self) -> Path:
        return self._path

    def set_field(self, table: str, key: str, value: object) -> None:
        """Update one semantic field and reflect it in both model and document."""
        # Update tomlkit document
        doc = self._raw
        if table:
            target = doc
            for segment in table.split("."):
                if segment not in target:
                    target[segment] = tomlkit.table()
                target = target[segment]
            target[key] = value
        else:
            doc[key] = value

        # Reload model from updated document
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tf:
            tf.write(tomlkit.dumps(doc))
            tf.flush()
            temp_path = Path(tf.name)
        try:
            self._model = load_project_config(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def write(self) -> None:
        """Write the document back to disk atomically."""
        text = tomlkit.dumps(self._raw)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self._path)

    @classmethod
    def open(cls, path: Path) -> ConfigDocument:
        """Open an existing config document for round-trip editing."""
        return cls(path)


def open_config_document(path: Path) -> ConfigDocument:
    """Open an existing Archledger config document for round-trip editing."""
    return ConfigDocument.open(path)


__all__ = ["ConfigDocument", "open_config_document"]
