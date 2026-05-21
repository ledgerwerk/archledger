Build and export
================

Native builds
-------------

.. code-block:: bash

   archledger build --format markdown
   archledger build --format asciidoc

``[build].default_output_dir`` is relative to the directory containing
``archledger.toml`` or ``.archledger.toml``. The default generated output
location remains ``.archledger/build/``.

Converter-backed exports
------------------------

- Markdown source uses ``pandoc`` for HTML, DOCX, RST, Textile, PDF, and AsciiDoc.
- AsciiDoc source uses ``asciidoctor`` for HTML.
- AsciiDoc source uses ``asciidoctor-pdf`` for PDF.
- AsciiDoc source uses Asciidoctor DocBook plus ``pandoc`` for DOCX, Markdown, RST, and Textile.

These export paths are supported when the external tools are installed and the
corresponding integration checks pass. Native Markdown and AsciiDoc assembly
remain the lowest-friction path because they do not depend on external converters.

Source migration
----------------

``source convert`` migrates Markdown-source projects to AsciiDoc-source projects.
Write mode is strict by default and requires ``pandoc``:

.. code-block:: bash

   archledger source convert --to asciidoc --apply

For an explicit temporary mixed-body migration:

.. code-block:: bash

   archledger source convert --to asciidoc --apply --allow-mixed-body-format
