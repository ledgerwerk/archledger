BDD and Gherkin
===============

Archledger stores BDD as metadata on existing records. It can import and export
Gherkin ``.feature`` files, but it does not run a BDD runtime.

Canonical ownership
-------------------

- Archledger records are the canonical architecture and specification records.
- SpecWeave-owned files under ``specs/behavior/features`` may be the canonical behavior specifications.
- Archledger-exported ``.feature`` files are derived unless a project explicitly changes ownership.
- ``test_refs`` point at executable pytest validation and remain separate from behavior-spec ownership.

Supported Gherkin subset
------------------------

Supported constructs:

- ``Feature:``
- ``Rule:``
- ``Scenario:`` and ``Example:``
- tags
- ``Given`` / ``When`` / ``Then`` / ``And`` / ``But``

Unsupported constructs:

- ``Background:``
- ``Scenario Outline:`` / ``Scenario Template:``
- ``Examples:``
- data tables
- doc strings

Mutation safety
---------------

Use ``archledger bdd set`` and ``archledger bdd link`` instead of editing YAML by
hand. These commands reject invalid automation statuses, unsafe feature paths,
and unsafe pytest test references before writing any front matter.

Drift detection
---------------

``archledger bdd sync --check`` compares linked feature files against Archledger
metadata. Invalid linked feature files are reported as explicit sync findings; a
parse failure is never treated as “no drift”.

