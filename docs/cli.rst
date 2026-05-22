CLI guide
=========

Key commands
------------

``--json`` is a global option, so place it before the subcommand:
``archledger --json read ...`` rather than ``archledger read --json``.

Initialize a workspace:

.. code-block:: bash

   archledger init --source-format markdown
   archledger init --source-format asciidoc

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

``check`` is read-only. It validates numbering and integrity but does not mutate counters or source files.

Build output:

.. code-block:: bash

   archledger build --format markdown
   archledger build --format asciidoc
   archledger build --format html --format markdown
