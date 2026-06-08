"""Load published archledger JSON Schema documents."""

from __future__ import annotations

import json
from importlib.resources import files

from archledger.errors import ArchledgerError

SCHEMA_FILES = {
    "record": "archledger.record.v2.schema.json",
    "sdd": "archledger.sdd.v1.schema.json",
    "sdd-status": "archledger.sdd-status.v2.schema.json",
    "sdd-policy": "archledger.sdd-policy.v1.schema.json",
    "sdd-coverage": "archledger.sdd-coverage.v1.schema.json",
    "sdd-pr": "archledger.sdd-pr.v1.schema.json",
    "sdd-init": "archledger.sdd-init.v1.schema.json",
    "sdd-explain": "archledger.sdd-explain.v1.schema.json",
    "sdd-check": "archledger.sdd-check.v2.schema.json",
    "context": "archledger.context.v1.schema.json",
    "trace": "archledger.trace.v1.schema.json",
    "changed": "archledger.changed.v1.schema.json",
    "bdd-import": "archledger.bdd-import.v1.schema.json",
    "bdd-export": "archledger.bdd-export.v1.schema.json",
    "bdd-status": "archledger.bdd-status.v1.schema.json",
    "bdd-list": "archledger.bdd-list.v1.schema.json",
    "bdd-validate": "archledger.bdd-validate.v1.schema.json",
    "bdd-sync": "archledger.bdd-sync.v1.schema.json",
}


def load_json_schema(target: str) -> dict[str, object]:
    filename = SCHEMA_FILES.get(target)
    if filename is None:
        raise ArchledgerError(
            "schema target must be one of: " + ", ".join(sorted(SCHEMA_FILES))
        )
    resource = files("archledger").joinpath("schemas", filename)
    return json.loads(resource.read_text(encoding="utf-8"))


__all__ = ["SCHEMA_FILES", "load_json_schema"]
