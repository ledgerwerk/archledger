@area-storage @feature-frontmatter-and-storage
Feature: Front matter and storage primitives

  # Record storage must preserve YAML front matter, body text, configured source
  # extensions, and storage metadata without accepting ambiguous boolean values
  # where integers are required.

  @rule-frontmatter-read-write
  Rule: Front matter documents round-trip across supported source formats

    @bdd-frontmatter-read-markdown-valid
    Example: Markdown front matter document is read correctly
      Given a markdown record with YAML front matter and body text
      When read_front_matter_document is called
      Then metadata and body text are returned separately

    @bdd-frontmatter-write-markdown-roundtrip
    Example: Markdown front matter document writes and reads back
      Given metadata and body text for a markdown record
      When write_front_matter_document writes the record
      Then reading the record returns the same metadata and body

    @bdd-frontmatter-read-asciidoc-valid
    Example: AsciiDoc front matter document is accepted
      Given an asciidoc record with YAML front matter and body text
      When read_front_matter_document is called
      Then metadata and body text are returned separately

    @bdd-frontmatter-write-asciidoc-roundtrip
    Example: AsciiDoc front matter document writes and reads back
      Given metadata and body text for an asciidoc record
      When write_front_matter_document writes the record
      Then reading the record returns the same metadata and body

  @rule-frontmatter-errors
  Rule: Invalid front matter fails clearly

    @bdd-frontmatter-missing-rejected
    Example: Missing front matter is rejected
      Given a record body without YAML front matter delimiters
      When read_front_matter_document is called
      Then a front matter error is raised

    @bdd-frontmatter-non-mapping-rejected
    Example: Non-mapping YAML front matter is rejected
      Given a record with YAML front matter that is a list
      When read_front_matter_document is called
      Then a front matter error is raised

  @rule-source-file-iteration
  Rule: Source file iteration respects configured extensions

    @bdd-storage-iter-source-files-extension-filter
    Example: Source file iteration filters by extension
      Given a workspace with markdown, asciidoc, and unrelated files
      When iter_source_files is called for markdown source format
      Then only configured markdown source files are returned

  @rule-storage-meta
  Rule: Storage metadata preserves counter floors and rejects boolean integers

    @bdd-storage-meta-version-two-required
    Example: Storage metadata must use schema version 2
      Given storage metadata with an unsupported version
      When the metadata is read
      Then a storage error is raised

    @bdd-storage-meta-next-number-bool-rejected
    Example: Boolean next number is rejected
      Given storage metadata with next_number set to true
      When the metadata is read
      Then a storage error is raised

    @bdd-storage-meta-counter-floor-preserved
    Example: Counter recomputation preserves the existing floor
      Given storage metadata with next_number higher than existing records
      When next number is recomputed
      Then the stored counter floor is preserved

  @rule-atomic-write
  Rule: Atomic writes replace contents without leaving temporary files

    @bdd-storage-atomic-write-cleanup
    Example: Atomic write leaves no temporary files behind
      Given an existing text file
      When write_text_atomic replaces the file contents
      Then the file contains the new contents
      And no temporary sibling files remain
