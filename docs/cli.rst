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

   archledger --json where
   archledger --json status
   archledger --json check
   archledger --json read --include-body --include-draft

Track implementation drift:

.. code-block:: bash

   archledger --json snapshot --reason after-archledger-update
   archledger --json changed

Create records:

.. code-block:: bash

   archledger new requirement --title "Render architecture document" --status proposed
   archledger new adr --title "Treat source fragments as canonical" --status proposed

Build output:

.. code-block:: bash

   archledger build --format markdown
   archledger build --format asciidoc
   archledger build --formats html,markdown
