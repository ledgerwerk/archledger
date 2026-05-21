Configuration
=============

Configuration lives in ``archledger.toml``.

Important sections
------------------

- ``[source]`` controls the canonical source dialect and extensions.
- ``[build]`` controls default output behavior and converter selection.
- ``[tracking]`` controls workspace snapshots and change detection.
- ``[arc42]`` controls document metadata defaults.
- ``[skill]`` points agents at the repository skill file.

Example
-------

.. code-block:: toml

   config_version = 5
   archledger_dir = ".archledger"

   [source]
   format = "markdown"
   section_extension = ".md"
   record_extension = ".md"
   schema_version = 2

   [build]
   default_output = "architecture.md"
   default_format = "markdown"
   default_output_dir = "build"
   converter = "auto"

   [tracking]
   enabled = true
   state_file = "source-state.json"
   scanner = "auto"

``[build].default_output_dir`` is relative to the directory containing
``archledger.toml`` or ``.archledger.toml``.

``source-state.json`` stores SHA-256 content hashes only for files. It does not
persist mtimes or file sizes. Directory hashes are derived from file hashes.

Per-output overrides
--------------------

Use ``[build.outputs.<format>]`` for format-specific settings. Supported keys are
``tool``, ``pdf_engine``, ``reference_docx``, and ``enabled``.
