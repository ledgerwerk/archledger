"""BDD / Gherkin behavior-metadata layer for archledger.

BDD is treated as metadata on existing records (primarily
``runtime_scenario`` and ``quality_scenario``).  Gherkin ``.feature`` files
are an imported/exported exchange and automation format, never archledger's
canonical source of truth.  archledger does **not** run Cucumber or any BDD
runner; no such dependency is introduced here.

See README.md and docs/agent-workflow.rst for the public workflow contract.
"""

from archledger.bdd.models import BddAutomation, BddExample
from archledger.bdd.normalize import normalize_bdd_metadata

__all__ = ["BddAutomation", "BddExample", "normalize_bdd_metadata"]
