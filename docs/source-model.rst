Source model
============

Canonical source
----------------

The source of truth is the fragment tree under ``archledger_dir``:

- ``sections/`` for the major arc42 chapter skeleton
- ``records/`` for individual architecture facts
- ``archive/`` for archived records and tombstones that preserve allocated ledger IDs

Records include structural, behavioral, and decision artifacts plus first-class
``diagram`` records. Diagram records default to plain text diagrams (``diagram_type = "text"``).
Text diagrams stay embedded in Markdown/AsciiDoc record bodies as readable fenced blocks.
Mermaid is available for compact sequence, state, or flow diagrams but is not the default.

Fragments contain YAML front matter and a body in the configured dialect.
Archived fragments keep normal front matter and use ``status: archived``.

Ledger ID format
----------------

Default IDs use ``<prefix>_<number>`` (for example ``al_0013``).

When ``[ids].segment_mode = "type"``, IDs use
``<prefix>_<segment>_<number>`` (for example ``al_content_0013`` and
``al_risk_0014``). Segment values come from metadata/config mapping, while
the numeric sequence remains one global ledger-wide counter.

Traceability
------------

Use ``source_refs`` when fragments describe real files or directories.
Directory refs must end with ``/`` and must exist in the workspace.

Generated output
----------------

Generated build outputs are derived artifacts and should not be edited as
source. The default location is ``.archledger/build/``, but
``[build].default_output_dir`` may place them elsewhere under the project root.
