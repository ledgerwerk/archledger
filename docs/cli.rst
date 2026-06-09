CLI guide
=========

``--json`` is a global option, so place it before the subcommand:
``archledger --json read ...`` rather than ``archledger read --json``.

Profiles and SDD
----------------

``archledger init --profile arc42|sdd`` selects the default profile for a new
project. Existing projects can run ``archledger profile migrate arc42 --write``
to move legacy sections into ``.archledger/profiles/arc42/sections``.

Use ``archledger sdd check --strict`` to enforce traceability and
``archledger sdd status`` to report coverage. ``archledger context`` creates
compact record context for a file, record, or changed source set.
``archledger trace RECORD_ID`` follows incoming and outgoing links.

For pull requests, use ``source changed --against REVISION`` or
``sdd check-pr --against REVISION``. Mutation commands are grouped under
``record``, ``refs``, ``links``, and ``ac``. JSON Schemas are returned with
``schema --format jsonschema --target TARGET``. ``install`` creates optional
integration scaffolds and refuses overwrites unless ``--force`` is supplied.


BDD / Gherkin
-------------

BDD is treated as **metadata on existing records** (primarily ``runtime_scenario``
and ``quality_scenario``).  Gherkin ``.feature`` files are an imported/exported
exchange and automation format; archledger does **not** run Cucumber or any BDD
runner.

Import a feature file as behavior records:

.. code-block:: bash

   archledger bdd import specs/behavior/features/task-management/plan-gates.feature \
     --kind runtime-scenario --status proposed

Export a record with ``bdd`` metadata as a deterministic ``.feature`` file:

.. code-block:: bash

   archledger bdd export al_runtime_0123 \
     --out specs/behavior/features/task-management/plan-gates.derived.feature

Imported records carry a ``bdd`` front-matter block (feature, rule, scenario,
tags, given/when/then, automation) and a ``source_refs`` entry with role
``documents`` linking to the originating feature file.  Imported records default
to ``automation.status=linked`` since a feature file and scenario are now bound.
Keep behavior specs in ``source_refs`` and plain pytest enforcement in
``test_refs``.

Automation status semantics: ``pending`` (no wiring yet), ``linked`` (a feature
file/scenario is bound but no executable runner), ``automated`` (a runner command
is recorded and intended to be executed externally), and ``not_applicable``
(deliberately manual). Under ``require_bdd_automation_for_accepted_records``
(enabled by ``sdd init --strict-defaults``), a record must reach ``automated`` or
``not_applicable``; ``linked`` alone is treated as not-yet-automated and produces
an ``SDD-BDD-AUTOMATION`` error. Under ``--strict``, ``linked`` without
executable ``test_refs`` is a warning, which still fails the strict run. SDD
coverage reports ``behavior_linked`` and ``behavior_automated`` as separate
dimensions for the same reason.

**Canonical ownership**: Archledger records are the canonical
architecture/specification records. SpecWeave-owned files under
``specs/behavior/features`` may be the canonical behavior specifications.
Archledger-exported ``.feature`` files are derived unless a project explicitly
changes ownership. ``bdd sync --check`` reports drift between linked behavior
specs and Archledger metadata.

For the supported Gherkin subset and ownership details, see :doc:`bdd-gherkin`.

Additional BDD commands:

.. code-block:: bash

   # Validate BDD metadata on a record or feature file
   archledger bdd validate al_runtime_0042
   archledger bdd validate --feature-file specs/behavior/features/task-management/plan-gates.feature
   archledger bdd validate --all

   # List all records with BDD metadata (filterable)
   archledger bdd list
   archledger bdd list --automation linked
   archledger bdd list --feature "Task lifecycle"

   # Summarize BDD coverage
   archledger bdd status

   # Set or replace the bdd block on a record (no manual YAML)
   archledger bdd set al_runtime_0042 \
     --feature "Task lifecycle" --scenario "Blocked" \
     --given "a task has a proposed plan" \
     --when "the agent starts implementation" \
     --then "implementation is blocked" \
     --tag task-0001

   # Link automation metadata, source_refs, and pytest test_refs
   archledger bdd link al_runtime_0042 \
     --feature-file specs/behavior/features/task-management/plan-gates.feature \
     --scenario "@bdd-implementation-blocked-before-plan-acceptance" \
     --test tests/test_task_management_plan_gates.py::test_agent_cannot_start_implementation_before_plan_approval \
     --status automated

   # Dry-run import (parse without creating records)
   archledger bdd import specs/behavior/features/task-management/plan-gates.feature --dry-run

   # Batch export all BDD records grouped by feature+rule
   archledger bdd export --all --out-dir specs/behavior/features/derived

Use ``archledger --json read --body`` as the agent source of truth for BDD
records; Archledger-exported ``.feature`` files are derived artifacts.


.. _init:

``init`` — Initialize a workspace
---------------------------------

Creates ``archledger.toml``, the state directory, section stubs, record-type
subdirectories, and ``storage.yaml`` in one step.

Fails if a config file already exists in the target workspace.

Synopsis
^^^^^^^^

.. code-block:: bash

   archledger init [OPTIONS]

Quick start
^^^^^^^^^^^

.. code-block:: bash

   # Markdown project
   archledger init --source-format markdown

   # AsciiDoc project (default when --source-format is omitted)
   archledger init --source-format asciidoc

What init creates
^^^^^^^^^^^^^^^^^

Running ``init`` produces:

- ``archledger.toml`` — project configuration (see :doc:`configuration`)
- ``<archledger-dir>/`` — state directory (default ``.archledger``)
- ``<archledger-dir>/sections/`` — 12 arc42 section stubs (default ``al_0001`` through ``al_0012``)
- ``<archledger-dir>/records/`` — typed subdirectories:

  ``building_blocks``, ``concepts``, ``constraints``, ``contexts``,
  ``decisions``, ``deployment``, ``diagrams``, ``glossary``,
  ``quality_goals``, ``quality_requirements``, ``quality_scenarios``,
  ``requirements``, ``risks``, ``runtime``, ``stakeholders``, ``strategy``

- ``<archledger-dir>/archive/`` — for archived records
- ``<archledger-dir>/build/`` — default build output directory
- ``<archledger-dir>/storage.yaml`` — ledger counter state

Section files are numbered by configured ``[ids]`` format (default ``al_0001`` through ``al_0012``) matching the 12
major arc42 sections:

1. Introduction and Goals
2. Architecture Constraints
3. Context and Scope
4. Solution Strategy
5. Building Block View
6. Runtime View
7. Deployment View
8. Cross-cutting Concepts
9. Architecture Decisions
10. Quality Requirements
11. Risks and Technical Debt
12. Glossary

After init, add starter content with:

.. code-block:: bash

   archledger seed arc42-minimal

Core options
^^^^^^^^^^^^

``--source-format FORMAT``
   Canonical source dialect: ``markdown`` or ``asciidoc``.
   Default: ``asciidoc``.
   Determines file extensions, default build output name, and template
   rendering for all generated section stubs.

``--archledger-dir PATH``
   State directory to create, relative to the config path unless absolute.
   Default: ``.archledger``.
   Use an absolute path to store state outside the project tree.

``--project-name TEXT``
   Stable project identity stored in ``archledger.toml``.
   Defaults to the workspace directory basename (slug-normalized).

``--project-uuid TEXT``
   Stable project UUID. Auto-generated when omitted.
   Must be a valid UUID format.

``--id-prefix TEXT``
   Ledger ID prefix for generated section/record IDs (for example ``al`` or ``ta``).
   Default: ``al``.

``--id-width N``
   Minimum digit width for generated ledger IDs.
   Default: ``4``.

``--id-segment-mode MODE``
   Ledger ID segment mode: ``none`` or ``type``.
   Default: ``none``.

Build options
^^^^^^^^^^^^^

``--build-default-format FORMAT``
   Default build output format: ``markdown``, ``asciidoc``, ``pdf``, or ``docx``.
   When omitted, defaults to the source format.

``--build-default-output FILENAME``
   Default build output filename.
   When omitted, defaults to ``architecture.<ext>`` matching the source format.

``--build-default-output-dir DIR``
   Build output directory, relative to the config path.
   Default: ``build``.

``--build-include-draft``
   Include draft records in build output.

``--build-include-superseded``
   Include superseded records in build output.

``--build-strict``
   Enable strict build mode.

``--build-keep-intermediate``
   Keep intermediate build files.

``--build-converter TOOL``
   Build converter tool: ``auto``, ``pandoc``, or ``asciidoctor``.
   Default: ``auto``.

``--build-pdf-engine ENGINE``
   PDF engine for pandoc builds.

``--build-reference-docx PATH``
   Reference docx template for pandoc builds.

Diagram options
^^^^^^^^^^^^^^^

``--diagrams`` / ``--no-diagrams``
   Enable diagram support.
   Default: ``--no-diagrams``.

``--diagram-renderer RENDERER``
   Diagram renderer: ``pass-through``, ``mermaid-cli``, or
   ``asciidoctor-diagram``.
   Default: ``pass-through``.

``--diagram-default-type TYPE``
   Default diagram type: ``text``, ``ascii``, ``unicode``, ``svgbob``, or
   ``mermaid``.
   Default: ``text``.

``--diagram-output-dir DIR``
   Diagram output directory.
   Default: ``diagrams``.

``--diagram-image-format FORMAT``
   Diagram image format: ``svg`` or ``png``.
   Default: ``svg``.

``--diagram-kroki-url URL``
   Kroki server URL (reserved for future renderers).

arc42 options
^^^^^^^^^^^^^

``--arc42-title TEXT``
   arc42 template title.
   Default: ``Architecture Documentation``.

``--arc42-language CODE``
   arc42 template language.
   Default: ``en``.

``--arc42-template-version VERSION``
   arc42 template version.
   Default: ``9.0-EN``.

``--arc42-include-help`` / ``--no-arc42-include-help``
   Include arc42 help sections in generated section stubs.
   Default: ``--no-arc42-include-help``.

Tracking options
^^^^^^^^^^^^^^^^

``--tracking`` / ``--no-tracking``
   Enable source tracking.
   Default: ``--tracking``.

``--tracking-scanner SCANNER``
   Tracking scanner: ``auto``, ``git``, or ``filesystem``.
   Default: ``auto``.

``--tracking-state-file FILENAME``
   Tracking state filename.
   Default: ``source-state.json``.

``--tracking-max-file-bytes N``
   Maximum file size in bytes for tracking.
   Default: ``1000000``.

``--tracking-include GLOB``
   Glob pattern for tracking includes. Repeatable.

``--tracking-exclude GLOB``
   Glob pattern for tracking excludes. Repeatable.

Examples
^^^^^^^^

Minimal Markdown project with build output at the project root:

.. code-block:: bash

   archledger init --source-format markdown \
     --build-default-output ARCHITECTURE.md \
     --build-default-output-dir .

AsciiDoc project with diagram support, German arc42 template, and custom
tracking excludes:

.. code-block:: bash

   archledger init --source-format asciidoc \
     --diagrams \
     --diagram-default-type mermaid \
     --arc42-title "Meine Systemarchitektur" \
     --arc42-language de \
     --tracking-exclude "vendor/**" \
     --tracking-exclude "**/__pycache__/**"

External state directory:

.. code-block:: bash

   archledger init --archledger-dir /shared/archledger-state

Segmented IDs for record-type-based naming:

.. code-block:: bash

   archledger init --source-format markdown --id-segment-mode type

JSON output for automation:

.. code-block:: bash

   archledger --json init --source-format markdown

.. _other-commands:

Other commands
--------------

Inspect the current source state:

.. code-block:: bash

   archledger --json paths
   archledger --json status
   archledger --json check
   archledger --json doctor
   archledger --json read --body --include-drafts

Track implementation drift:

.. code-block:: bash

   archledger --json source snapshot --reason after-archledger-update
   archledger --json source changed

Create records:

.. code-block:: bash

   archledger new requirement "Render architecture document" --status proposed
   archledger new adr "Treat source fragments as canonical" --status proposed
   archledger new diagram "Runtime login flow" --section runtime_view --status proposed

Archive and repair:

.. code-block:: bash

   archledger archive al_0022 --reason "obsolete after al_0041"
   archledger doctor
   archledger doctor --repair

Renumber IDs and references:

.. code-block:: bash

   archledger renumber --prefix ta --width 3
   archledger renumber --prefix ta --width 3 --apply
   archledger renumber --id-segment-mode type
   archledger renumber --id-segment-mode type --apply
   archledger renumber --id-segment-mode none --apply

``check`` is read-only. It validates numbering and integrity but does not mutate counters or source files.

Build output:

.. code-block:: bash

   archledger build --format markdown
   archledger build --format asciidoc
   archledger build --format html --format markdown
