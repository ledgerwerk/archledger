CLI guide
=========

``--json`` is a global option, so place it before the subcommand:
``archledger --json read ...`` rather than ``archledger read --json``.

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
