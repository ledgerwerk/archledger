SDD
===

The ``sdd`` profile turns Archledger into a traceability and validation policy
checker for accepted records.

Lifecycle
---------

Common commands:

.. code-block:: bash

   archledger sdd init --strict-defaults --seed minimal
   archledger sdd policy show
   archledger sdd policy set --require-bdd-automation
   archledger sdd check
   archledger sdd check --strict
   archledger sdd check-pr --against origin/main
   archledger sdd status
   archledger sdd coverage --include-bdd
   archledger sdd coverage --format markdown
   archledger sdd explain SDD-BDD-AUTOMATION
   archledger sdd waive add al_0013 --rule SDD-REQ-AC --reason "Legacy gap."

BDD automation policy
---------------------

``bdd.automation.status`` has four supported values:

- ``pending`` — behavior metadata exists, but no linked feature file or runner is wired yet.
- ``linked`` — the canonical feature file and scenario are linked, but no executable runner is recorded yet.
- ``automated`` — executable validation is wired and should be reflected in ``test_refs``.
- ``not_applicable`` — the behavior is intentionally manual or non-automatable.

The policy meanings are:

- default policy: ``linked`` is acceptable traceability; ``pending`` warns
- ``--strict``: ``linked`` without executable ``test_refs`` warns and fails the strict run
- ``--require-bdd-automation`` (or ``sdd init --strict-defaults``): ``pending`` and ``linked`` are errors

Coverage
--------

``archledger sdd coverage`` reports aggregate coverage for accepted requirements,
ADRs, risks, and optional BDD dimensions. Use ``--format markdown`` for a
copy-pastable report and ``--by-record`` with ``--json`` when automation needs
per-record gaps.
