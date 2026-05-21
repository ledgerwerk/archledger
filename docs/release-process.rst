Release process
===============

This checklist is for maintainers preparing a beta or public release.

Pre-release checks
------------------

Run the standard quality gates from a clean checkout:

.. code-block:: bash

   python -m pip install -e ".[dev,docs]"
   python -m pytest -q
   python -m ruff check .
   python -m mypy archledger
   python -m sphinx -b html docs docs/_build/html

Build and metadata validation
-----------------------------

Build the actual distribution artifacts and verify their metadata:

.. code-block:: bash

   rm -rf dist build *.egg-info
   python -m build
   python -m twine check dist/*

Installed-wheel smoke test
--------------------------

Always verify the built wheel from outside the source checkout:

.. code-block:: bash

   python -m venv /tmp/archledger-wheel-test
   /tmp/archledger-wheel-test/bin/python -m pip install dist/*.whl
   /tmp/archledger-wheel-test/bin/python -I - <<'PY'
   import importlib.metadata
   import archledger

   assert importlib.metadata.version("archledger") == archledger.__version__
   print(archledger.__version__)
   PY
   workdir="$(mktemp -d)"
   cd "$workdir"
   /tmp/archledger-wheel-test/bin/archledger --version
   /tmp/archledger-wheel-test/bin/archledger init --source-format markdown
   /tmp/archledger-wheel-test/bin/archledger seed arc42-minimal
   /tmp/archledger-wheel-test/bin/archledger new requirement --title "Smoke" --status accepted
   /tmp/archledger-wheel-test/bin/archledger build --format markdown
   /tmp/archledger-wheel-test/bin/archledger --json read --body

Converter-backed release confidence
-----------------------------------

If the release promises converter-backed exports, run the optional integration coverage in an environment with the tools installed:

.. code-block:: bash

   python -m pytest -q -m integration tests/test_converter_integration.py

Release decision
----------------

Before tagging or publishing:

1. Confirm the changelog is updated.
2. Confirm CI is green on the supported Python versions.
3. Confirm the built artifact version matches ``archledger.__version__`` when installed.
4. Confirm the installed console script works outside the repository checkout.
