Agent workflow
==============

SDD workflow
------------

Before editing architecture-sensitive code:

1. Run ``archledger context --for-file PATH`` or
   ``archledger context --changed``.
2. Run ``archledger trace RECORD_ID`` for affected requirements or decisions.
3. Keep source-ref roles, test refs, acceptance criteria, and links current.
4. Run ``archledger source changed --fail-on-unlinked``.
5. Run ``archledger sdd check --strict``.

In pull-request automation, compare with the target branch using
``archledger sdd check-pr --against origin/main``.

Recommended loop
----------------

1. Run ``archledger --json paths``.
2. Run ``archledger --json source changed`` before broad architecture refreshes.
3. Run ``archledger --json read --body --include-drafts``.
4. Edit only the fragment files under ``sections/`` and ``records/``.
5. Run ``archledger --json check``.
6. Build only when the user needs an exported artifact.
7. Run ``archledger --json source snapshot --reason after-archledger-update`` after the updates have been validated.

Rules
-----

- Treat the fragment tree as the source of truth.
- Do not edit generated build output as source; determine its location from ``archledger --json paths`` and ``[build].default_output_dir``.
- Add ``source_refs`` when a fragment describes concrete implementation artifacts.

Three-tool boundary
-------------------

Archledger owns durable architecture and specification records. It may store
external Taskledger IDs, SpecWeave behavior references, pytest references, and
evidence paths as traceability data, but it does not execute Taskledger,
SpecWeave, pytest, behave, or Cucumber commands.

Taskledger owns active work state and task lifecycle. Store Taskledger
provenance as stable IDs such as ``task-0037`` only. Archledger validates the ID
shape and does not require the task to exist locally.

SpecWeave owns canonical Gherkin behavior specs and normalized behavior
evidence. When behavior specs explain an Archledger record, use ``source_refs``
that point at ``specs/behavior/features/.../*.feature``. When automation
validates a record, use ``test_refs`` that point at plain pytest tests.
