"""Load published archledger JSON Schema documents."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import cast

from archledger.errors import ArchledgerError

SCHEMA_FILES = {
    "record": "archledger.record.v4.schema.json",
    "record-v2": "archledger.record.v2.schema.json",
    "context": "archledger.context.v1.schema.json",
    "context-v2": "archledger.context.v2.schema.json",
    "trace": "archledger.trace.v1.schema.json",
    "changed": "archledger.changed.v2.schema.json",
    "changed-v1": "archledger.changed.v1.schema.json",
}


def load_json_schema(target: str) -> dict[str, object]:
    filename = SCHEMA_FILES.get(target)
    if filename is None:
        raise ArchledgerError(
            "schema target must be one of: " + ", ".join(sorted(SCHEMA_FILES))
        )
    resource = files("archledger").joinpath("schemas").joinpath(filename)
    return cast("dict[str, object]", json.loads(resource.read_text(encoding="utf-8")))


__all__ = ["SCHEMA_FILES", "load_json_schema"]
