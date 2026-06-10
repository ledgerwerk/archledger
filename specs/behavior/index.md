# Behavior index

Generated from `specs/behavior/features`.

## assembly

### Build format conversion and output selection
- Path: `specs/behavior/features/assembly/build-format-conversion.feature`

#### Rule: Native outputs avoid external conversion tools

- `bdd-build-markdown-native-without-tools` Markdown source builds markdown without external tools -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-asciidoc-native-without-tools` AsciiDoc source builds AsciiDoc without external tools -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-native-uses-configured-output` Native build uses configured default output -> `tests/test_assembly_build_format_conversion.py` (missing)

#### Rule: Tool-backed formats fail with actionable install hints

- `bdd-build-html-requires-asciidoctor` HTML output requires asciidoctor -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-pdf-requires-asciidoctor-pdf` PDF output requires asciidoctor-pdf -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-docx-requires-pandoc` DOCX output requires pandoc -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-pandoc-format-requires-asciidoctor` Pandoc-backed output still requires asciidoctor for AsciiDoc source -> `tests/test_assembly_build_format_conversion.py` (missing)

#### Rule: Conversion commands are generated deterministically

- `bdd-build-docbook-intermediate-before-pandoc` Pandoc-backed formats use DocBook as intermediate -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-output-extension-infers-format` Explicit output extension infers requested format -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-mermaid-renderer-only-when-enabled` Mermaid rendering is invoked only when diagram rendering is enabled -> `tests/test_assembly_build_format_conversion.py` (missing)

#### Rule: Multiple output selection obeys config and CLI precedence

- `bdd-build-json-reports-multiple-outputs` JSON build reports every generated output -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-default-includes-enabled-outputs` Default build includes enabled configured outputs -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-all-skips-disabled-outputs` Build all honors disabled configured outputs -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-explicit-format-overrides-disabled-output` Explicit format can override a disabled configured output -> `tests/test_assembly_build_format_conversion.py` (missing)
- `bdd-build-rejects-multiple-formats-with-one-file` Multiple formats cannot share a single output file -> `tests/test_assembly_build_format_conversion.py` (missing)

### Document assembly
- Path: `specs/behavior/features/assembly/document-assembly.feature`
- Summary: The assembly command renders all records into a single arc42 document

#### Rule: Assembly produces a complete arc42 document

- `bdd-assembly-creates-output` Assembly writes an output file -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-includes-all-sections` Assembly includes all 12 arc42 major sections -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-includes-drafts` Assembly includes draft records when flag is set -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-excludes-drafts` Assembly excludes draft records by default -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-includes-superseded` Assembly includes superseded records when flag is set -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-schema` Assembly result includes source format -> `tests/test_assembly_document_assembly.py` (missing)

#### Rule: Assembly supports multiple output formats

- `bdd-assembly-format-from-extension` Output format is inferred from file extension -> `tests/test_assembly_document_assembly.py` (missing)
- `bdd-assembly-format-markdown` Markdown source produces markdown output -> `tests/test_assembly_document_assembly.py` (missing)

### Section rendering
- Path: `specs/behavior/features/assembly/section-rendering.feature`
- Summary: Section rendering assembles record data into structured arc42 sections

#### Rule: Building block view renders hierarchical structure

- `bdd-section-building-block-hierarchy` Building block hierarchy omits empty fields -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-building-block-with-fulfilled` Building block hierarchy includes fulfilled requirements when present -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-building-block-risks` Building block hierarchy includes risks when present -> `tests/test_assembly_section_rendering.py` (missing)

#### Rule: Section diagrams render diagram body and caption

- `bdd-section-diagram-body` Diagram section renders diagram body -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-diagram-caption` Diagram section renders caption -> `tests/test_assembly_section_rendering.py` (missing)

#### Rule: Overview sections render structured tables

- `bdd-section-requirements-overview` Requirements overview renders as a table -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-stakeholders-table` Stakeholders table renders contact info -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-quality-goals` Quality goals table renders priorities -> `tests/test_assembly_section_rendering.py` (missing)
- `bdd-section-glossary-table` Glossary table renders terms and definitions -> `tests/test_assembly_section_rendering.py` (missing)

## bdd

### BDD export generates Gherkin feature files from records
- Path: `specs/behavior/features/bdd/bdd-export.feature`
- Summary: The exporter renders deterministic Gherkin from BDD metadata, with

#### Rule: Single record export produces a valid feature file

- `bdd-export-creates-file` Record with valid BDD metadata exports a feature file -> `tests/test_bdd_bdd_export.py` (missing)
- `bdd-export-refuses-no-bdd` Record without BDD metadata cannot be exported -> `tests/test_bdd_bdd_export.py` (missing)
- `bdd-export-deterministic` Export is deterministic for the same record -> `tests/test_bdd_bdd_export.py` (missing)

#### Rule: Export enforces path and overwrite safety

- `bdd-export-refuses-absolute` Absolute output path is refused -> `tests/test_bdd_bdd_export.py` (missing)
- `bdd-export-refuses-overwrite` Existing file is refused without force -> `tests/test_bdd_bdd_export.py` (missing)

#### Rule: Batch export groups by feature and rule

- `bdd-export-all-multi-rule` Multiple rules are preserved in one feature file -> `tests/test_bdd_bdd_export.py` (missing)

#### Rule: Feature filenames are sanitized

- `bdd-export-safe-filename` Unsafe characters in feature names are collapsed -> `tests/test_bdd_bdd_export.py` (missing)
- `bdd-export-safe-filename-empty` Empty feature name falls back to a default -> `tests/test_bdd_bdd_export.py` (missing)
- `bdd-export-safe-output-file` Output file outside workspace is refused -> `tests/test_bdd_bdd_export.py` (missing)

### BDD import creates records from Gherkin feature files
- Path: `specs/behavior/features/bdd/bdd-import.feature`
- Summary: The importer reads a Gherkin feature file, creates one archledger

#### Rule: Import creates records with correct metadata

- `bdd-import-creates-records` Feature file with two scenarios creates two records -> `tests/test_bdd_bdd_import.py` (missing)
- `bdd-import-writes-body` Imported record body contains GWT steps -> `tests/test_bdd_bdd_import.py` (missing)
- `bdd-import-quality-scenario` Quality scenario kind is accepted -> `tests/test_bdd_bdd_import.py` (missing)

#### Rule: Import warns on edge cases

- `bdd-import-deprecated-path` Deprecated feature file path produces a warning -> `tests/test_bdd_bdd_import.py` (missing)
- `bdd-import-missing-steps` Scenarios missing GWT steps produce warnings -> `tests/test_bdd_bdd_import.py` (missing)

#### Rule: Import validates inputs

- `bdd-import-refuses-missing-file` Non-existent feature file raises FileNotFoundError -> `tests/test_bdd_bdd_import.py` (missing)
- `bdd-import-normalizes-kind` Hyphenated kind is normalized to underscore -> `tests/test_bdd_bdd_import.py` (missing)

### BDD inspection lists records and summarizes coverage
- Path: `specs/behavior/features/bdd/bdd-inspect.feature`
- Summary: The list and status commands produce structured summaries of BDD

#### Rule: BDD list enumerates records with BDD metadata

- `bdd-list-all-records` List returns all records with bdd metadata -> `tests/test_bdd_bdd_inspect.py` (missing)
- `bdd-list-filter-automation` Automation status filter narrows results -> `tests/test_bdd_bdd_inspect.py` (missing)
- `bdd-list-invalid-metadata` Invalid metadata entries are included but marked invalid -> `tests/test_bdd_bdd_inspect.py` (missing)

#### Rule: BDD status summarizes coverage dimensions

- `bdd-status-totals` Status reports totals for examples and invalid metadata -> `tests/test_bdd_bdd_inspect.py` (missing)
- `bdd-status-coverage` Coverage includes complete GWT, linked, automated, pending -> `tests/test_bdd_bdd_inspect.py` (missing)

### BDD metadata set and link commands
- Path: `specs/behavior/features/bdd/bdd-linking.feature`

#### Rule: BDD set creates or patches record metadata

- `bdd-set-creates-block` BDD set creates BDD block -> `tests/test_bdd_bdd_linking.py` (missing)
- `bdd-set-patches-existing-block` BDD set patches existing BDD block -> `tests/test_bdd_bdd_linking.py` (missing)

#### Rule: BDD link connects feature files, scenarios, automation, and tests

- `bdd-link-feature-source-ref` BDD link sets automation feature file and source ref -> `tests/test_bdd_bdd_linking.py` (missing)
- `bdd-link-pytest-test-ref` BDD link can add pytest test reference -> `tests/test_bdd_bdd_linking.py` (missing)
- `bdd-link-automated-requires-command-or-test` Automated status requires command or test reference -> `tests/test_bdd_bdd_linking.py` (missing)
- `bdd-link-refuses-record-without-bdd` BDD link refuses records without BDD metadata -> `tests/test_bdd_bdd_linking.py` (missing)
- `bdd-link-linked-default-status` BDD import or link defaults automation to linked -> `tests/test_bdd_bdd_linking.py` (missing)

### BDD metadata normalization and models
- Path: `specs/behavior/features/bdd/bdd-metadata.feature`
- Summary: The normalizer validates the `bdd` front-matter block, producing a

#### Rule: BDD models are immutable and hashable

- `bdd-models-frozen` BddExample and BddAutomation are frozen dataclasses -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-models-automation-defaults` BddAutomation defaults to status pending -> `tests/test_bdd_bdd_metadata.py` (missing)

#### Rule: Normalization validates structure and types

- `bdd-normalize-complete` Complete BDD block normalizes without warnings -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-none` None value returns no example and no warnings -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-non-mapping` Non-mapping value returns None with a warning -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-missing-required` Missing required fields produce warnings -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-wrong-types` Wrong types for fields produce warnings -> `tests/test_bdd_bdd_metadata.py` (missing)

#### Rule: Automation sub-block is validated independently

- `bdd-normalize-automation-default` Empty automation block defaults to pending -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-automation-invalid-status` Invalid automation status falls back to pending with a warning -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-automation-non-mapping` Non-mapping automation block is fatal -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-automation-feature-file-safety` Unsafe feature_file path is rejected -> `tests/test_bdd_bdd_metadata.py` (missing)
- `bdd-normalize-automation-command-type` Non-string command is rejected -> `tests/test_bdd_bdd_metadata.py` (missing)

### BDD path conventions detect deprecated locations
- Path: `specs/behavior/features/bdd/bdd-paths.feature`
- Summary: Path helpers identify deprecated BDD feature file locations and

#### Rule: Deprecated BDD feature paths are identified

- `bdd-paths-deprecated-prefixes` Paths under tests/bdd/features are deprecated -> `tests/test_bdd_bdd_paths.py` (missing)
- `bdd-paths-deprecated-behavior` Paths under tests/behavior/features are deprecated -> `tests/test_bdd_bdd_paths.py` (missing)
- `bdd-paths-deprecated-specs-bdd` Paths under specs/bdd/features are deprecated -> `tests/test_bdd_bdd_paths.py` (missing)

#### Rule: Recommended paths are not deprecated

- `bdd-paths-recommended-not-deprecated` Paths under specs/behavior/features are not deprecated -> `tests/test_bdd_bdd_paths.py` (missing)

#### Rule: Deprecation messages are explanatory

- `bdd-paths-deprecation-message` Deprecation message includes recommended path -> `tests/test_bdd_bdd_paths.py` (missing)

### BDD sync detects drift between records and feature files
- Path: `specs/behavior/features/bdd/bdd-sync.feature`
- Summary: Sync compares BDD metadata on records against linked Gherkin feature

#### Rule: Sync detects structural drift between records and feature files

- `bdd-sync-no-drift` Matching records and feature files produce no findings -> `tests/test_bdd_bdd_sync.py` (missing)
- `bdd-sync-file-missing` Linked feature file that does not exist is an error -> `tests/test_bdd_bdd_sync.py` (missing)
- `bdd-sync-scenario-missing` Record scenario absent from feature file is reported -> `tests/test_bdd_bdd_sync.py` (missing)
- `bdd-sync-gwt-mismatch` Modified GWT steps produce a mismatch finding -> `tests/test_bdd_bdd_sync.py` (missing)
- `bdd-sync-orphan-scenario` Extra scenarios in the feature file are reported as orphans -> `tests/test_bdd_bdd_sync.py` (missing)

#### Rule: Sync reports invalid BDD metadata

- `bdd-sync-invalid-metadata` Records with structurally invalid BDD metadata are reported -> `tests/test_bdd_bdd_sync.py` (missing)

#### Rule: Sync warns about deprecated feature paths

- `bdd-sync-deprecated-path` Deprecated feature file location produces a warning -> `tests/test_bdd_bdd_sync.py` (missing)

### BDD validation checks metadata and feature file structure
- Path: `specs/behavior/features/bdd/bdd-validate.feature`
- Summary: Validation inspects BDD metadata on records and parses Gherkin

#### Rule: Record BDD metadata is validated for completeness

- `bdd-validate-valid-record` Valid BDD metadata passes validation -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-absent-metadata` Absent BDD metadata is an error -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-gwt-incomplete` Missing given/when/then steps are reported -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-automation-status` Invalid automation status is an error -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-automated-no-command` Automated status without command or test_refs is a warning -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-linked-no-feature` Linked status without feature_file is a warning -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-tag-format` Empty or whitespace tags produce warnings -> `tests/test_bdd_bdd_validate.py` (missing)

#### Rule: Feature files are parse-validated

- `bdd-validate-feature-file` Valid feature file passes validation -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-feature-file-missing` Non-existent feature file is an error -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-feature-unsupported` Unsupported Gherkin constructs are reported -> `tests/test_bdd_bdd_validate.py` (missing)
- `bdd-validate-no-scenarios` Feature file with no scenarios is a warning -> `tests/test_bdd_bdd_validate.py` (missing)

#### Rule: All-records validation iterates the full ledger

- `bdd-validate-all-skip-no-bdd` Records without bdd metadata are skipped -> `tests/test_bdd_bdd_validate.py` (missing)

### Minimal Gherkin parser for archledger import
- Path: `specs/behavior/features/bdd/gherkin-parsing.feature`
- Summary: The parser handles Feature, Rule, Scenario/Example, tags, and

#### Rule: Supported constructs parse correctly

- `bdd-gherkin-feature-with-rule` Feature with Rule and multiple Scenarios -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-feature-without-rule` Feature without Rule -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-example-keyword` Example keyword is accepted -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-tags` Tags are applied to scenarios -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-and-but` And and But append to the last step bucket -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-multiple-rules` Multiple Rule blocks preserve per-scenario rule assignment -> `tests/test_bdd_gherkin_parsing.py` (missing)

#### Rule: Unsupported constructs raise clear errors

- `bdd-gherkin-rejects-no-feature` No Feature line raises GherkinSyntaxError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-multiple-features` Multiple Feature lines raise GherkinSyntaxError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-background` Background raises UnsupportedGherkinError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-scenario-outline` Scenario Outline raises UnsupportedGherkinError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-doc-string` Doc strings raise UnsupportedGherkinError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-data-table` Data tables raise UnsupportedGherkinError -> `tests/test_bdd_gherkin_parsing.py` (missing)
- `bdd-gherkin-rejects-orphan-and` And before any Given/When/Then raises GherkinSyntaxError -> `tests/test_bdd_gherkin_parsing.py` (missing)

## context

### Context CLI commands
- Path: `specs/behavior/features/context/context-cli.feature`
- Summary: The context CLI provides commands for building context packs for

#### Rule: Context changed uses source baseline for change detection

- `bdd-context-changed-baseline` Context changed uses source baseline without crashing -> `tests/test_context_context_cli.py` (missing)
- `bdd-context-changed-no-baseline` Context changed handles missing baseline gracefully -> `tests/test_context_context_cli.py` (missing)

#### Rule: Context file builds pack for a specific file

- `bdd-context-file-json` Context file returns JSON payload -> `tests/test_context_context_cli.py` (missing)

#### Rule: Context record builds pack for a specific record

- `bdd-context-record-json` Context record returns JSON payload -> `tests/test_context_context_cli.py` (missing)

### Context pack building for agents
- Path: `specs/behavior/features/context/context-pack.feature`
- Summary: Context packs provide focused architecture information for coding agents,

#### Rule: File context includes records whose source_refs match the file

- `bdd-context-file-matches-refs` Records with matching source_refs are included -> `tests/test_context_context_pack.py` (missing)
- `bdd-context-file-includes-linked` Linked records are included transitively -> `tests/test_context_context_pack.py` (missing)
- `bdd-context-file-caps-records` Context pack respects max_records limit -> `tests/test_context_context_pack.py` (missing)
- `bdd-context-file-schema` Context pack uses archledger.context.v1 schema -> `tests/test_context_context_pack.py` (missing)

#### Rule: Record context includes the record and its links

- `bdd-context-record-includes-links` Record context includes outgoing and incoming links -> `tests/test_context_context_pack.py` (missing)
- `bdd-context-record-not-found` Missing record returns empty context -> `tests/test_context_context_pack.py` (missing)

#### Rule: Changed context includes records impacted by file changes

- `bdd-context-changed-impacted` Changed files surface impacted records -> `tests/test_context_context_pack.py` (missing)

## diagrams

### Diagram validation and materialization
- Path: `specs/behavior/features/diagrams/diagram-validation-and-materialization.feature`

#### Rule: Diagram validation uses the source dialect and diagram type

- `bdd-diagram-markdown-mermaid-block-required` Markdown Mermaid diagram requires a fenced mermaid block -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-asciidoc-mermaid-block-required` AsciiDoc Mermaid diagram requires a mermaid literal block -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-empty-mermaid-block-warns` Empty Mermaid block is rejected as incomplete -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)

#### Rule: Text diagrams are default and validate readable source blocks

- `bdd-diagram-new-defaults-to-text` New diagram defaults to text type -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-configured-default-type` Configured diagram default type is honored -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-markdown-text-block-accepted` Markdown textdiagram block is accepted -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-asciidoc-source-block-accepted` AsciiDoc source block is accepted for text diagrams -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-empty-text-block-warns` Empty textdiagram block warns -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-overwide-text-line-warns` Overwide textdiagram line warns -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)

#### Rule: Diagram materialization is deterministic and explicit about renderer failure

- `bdd-diagram-materialize-markdown-mermaid` Markdown Mermaid block is rewritten to an image reference -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-materialize-asciidoc-mermaid` AsciiDoc Mermaid block is rewritten to an image reference -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-asset-name-content-hash` Diagram asset names are content-hash deterministic -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-mermaid-missing-actionable-error` Missing mermaid-cli produces actionable renderer error -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)
- `bdd-diagram-mermaid-still-supported` Mermaid remains supported when requested -> `tests/test_diagrams_diagram_validation_and_materialization.py` (missing)

## ids

### Ledger ID detection and filename mapping
- Path: `specs/behavior/features/ids/ledger-id-detection.feature`
- Summary: IDs can be detected in arbitrary text and mapped to filenames.

#### Rule: is_ledger_id identifies valid IDs in any context

- `bdd-ids-detect-valid` Valid ID string is recognized -> `tests/test_ids_ledger_id_detection.py` (missing)
- `bdd-ids-detect-invalid` Non-ID string is rejected -> `tests/test_ids_ledger_id_detection.py` (missing)
- `bdd-ids-detect-non-string` Non-string values are rejected -> `tests/test_ids_ledger_id_detection.py` (missing)

#### Rule: IDs map directly to filenames with the configured extension

- `bdd-ids-filename` Filename includes ID and extension -> `tests/test_ids_ledger_id_detection.py` (missing)
- `bdd-ids-from-filename` ID is extracted from filename stem -> `tests/test_ids_ledger_id_detection.py` (missing)

### Ledger ID format and parsing
- Path: `specs/behavior/features/ids/ledger-id-format.feature`
- Summary: Ledger IDs follow a configurable prefix_width pattern with optional

#### Rule: Ledger IDs are zero-padded integers with a configurable prefix

- `bdd-ids-format-zero-pad` Format pads numbers with leading zeros -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-format-custom-prefix` Format accepts custom prefix and width -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-format-rejects-invalid-number` Format rejects non-positive integers -> `tests/test_ids_ledger_id_format.py` (missing)

#### Rule: Ledger IDs can be parsed back to their numeric value

- `bdd-ids-parse-roundtrip` Parse reverses format for any valid ID -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-parse-custom-config` Parse respects configured prefix and width -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-parse-rejects-wrong-format` Parse rejects IDs that do not match configured format -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-parse-rejects-invalid` Parse rejects malformed ID strings -> `tests/test_ids_ledger_id_format.py` (missing)

#### Rule: Segmented IDs include a type segment between prefix and number

- `bdd-ids-segment-format` Format produces segmented IDs when segment mode is type -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-segment-parse` Parse extracts segment from segmented IDs -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-segment-requires-segment` Format requires a segment when segment mode is type -> `tests/test_ids_ledger_id_format.py` (missing)

#### Rule: ID components are validated on construction

- `bdd-ids-validate-prefix` Prefix must match lowercase alphanumeric pattern -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-validate-width` Width must be between 2 and 12 -> `tests/test_ids_ledger_id_format.py` (missing)
- `bdd-ids-validate-segment-mode` Segment mode must be none or type -> `tests/test_ids_ledger_id_format.py` (missing)

### ID segment mode configuration
- Path: `specs/behavior/features/ids/ledger-id-segments.feature`
- Summary: The segment mode determines whether IDs include a type segment between

#### Rule: Segment mode "none" produces flat IDs

- `bdd-ids-segment-none-format` Format produces flat ID when segment mode is none -> `tests/test_ids_ledger_id_segments.py` (missing)
- `bdd-ids-segment-none-ignores-segment` Format ignores segment parameter when mode is none -> `tests/test_ids_ledger_id_segments.py` (missing)

#### Rule: Segment mode "type" includes the type in the ID

- `bdd-ids-segment-type-format` Format includes type segment when mode is type -> `tests/test_ids_ledger_id_segments.py` (missing)
- `bdd-ids-segment-type-requires-segment` Format raises when segment is missing in type mode -> `tests/test_ids_ledger_id_segments.py` (missing)

#### Rule: Segment values are validated

- `bdd-ids-segment-validate-valid` Valid segment passes validation -> `tests/test_ids_ledger_id_segments.py` (missing)
- `bdd-ids-segment-validate-invalid` Invalid segment fails validation -> `tests/test_ids_ledger_id_segments.py` (missing)
- `bdd-ids-segment-validate-empty` Empty segment fails validation -> `tests/test_ids_ledger_id_segments.py` (missing)

## links

### Record link normalization
- Path: `specs/behavior/features/links/record-links.feature`
- Summary: Links describe directed relationships between records. Link normalization

#### Rule: Links are normalized from front-matter metadata

- `bdd-links-normalize-valid` Valid link is normalized correctly -> `tests/test_links_record_links.py` (missing)
- `bdd-links-normalize-invalid-rel` Invalid relationship type is rejected -> `tests/test_links_record_links.py` (missing)
- `bdd-links-normalize-empty-target` Empty target is rejected -> `tests/test_links_record_links.py` (missing)
- `bdd-links-normalize-none` None links returns empty tuple -> `tests/test_links_record_links.py` (missing)
- `bdd-links-normalize-non-list` Non-list links value is rejected -> `tests/test_links_record_links.py` (missing)
- `bdd-links-normalize-reason` Link reason is preserved -> `tests/test_links_record_links.py` (missing)

## migration

### Source format conversion
- Path: `specs/behavior/features/migration/source-format-conversion.feature`

#### Rule: Conversion requires explicit write for mutation

- `bdd-convert-requires-write` Conversion without write only plans changes -> `tests/test_migration_source_format_conversion.py` (missing)

#### Rule: Conversion requires Pandoc unless mixed body format is allowed

- `bdd-convert-write-requires-pandoc` Write conversion fails when Pandoc is missing -> `tests/test_migration_source_format_conversion.py` (missing)
- `bdd-convert-allow-mixed-without-pandoc` Mixed body format can bypass Pandoc -> `tests/test_migration_source_format_conversion.py` (missing)
- `bdd-convert-uses-pandoc-when-available` Pandoc is used for body conversion when available -> `tests/test_migration_source_format_conversion.py` (missing)

#### Rule: Conversion preserves current config and optional replacement behavior

- `bdd-convert-preserves-v5-config` Conversion preserves tracking and build config -> `tests/test_migration_source_format_conversion.py` (missing)
- `bdd-convert-replace-removes-old-files` Replace mode removes old source files -> `tests/test_migration_source_format_conversion.py` (missing)

## mutations

### Record mutation commands
- Path: `specs/behavior/features/mutations/record-mutations.feature`
- Summary: Patch-safe mutation commands modify individual record fields or body

#### Rule: Status can be changed on a record

- `bdd-mutation-set-status` Set status updates the record -> `tests/test_mutations_record_mutations.py` (missing)

#### Rule: Arbitrary metadata keys can be set

- `bdd-mutation-set-meta` Set meta updates a single key -> `tests/test_mutations_record_mutations.py` (missing)

#### Rule: Record body can be replaced or appended

- `bdd-mutation-replace-body` Replace body replaces entire content -> `tests/test_mutations_record_mutations.py` (missing)
- `bdd-mutation-append-body` Append body adds to existing content -> `tests/test_mutations_record_mutations.py` (missing)

#### Rule: Source references can be added to a record

- `bdd-mutation-add-source-ref` Add source ref appends a new reference -> `tests/test_mutations_record_mutations.py` (missing)

#### Rule: Mutations verify the record ID matches

- `bdd-mutation-wrong-id` Mutation rejects mismatched record ID -> `tests/test_mutations_record_mutations.py` (missing)

## records

### Model constants and format specs
- Path: `specs/behavior/features/records/model-constants.feature`
- Summary: The model module defines constants for source formats, output formats,

#### Rule: Source formats are markdown and asciidoc

- `bdd-model-valid-source-formats` Valid source formats include markdown and asciidoc -> `tests/test_records_model_constants.py` (missing)
- `bdd-model-source-format-extensions` Source format extensions map correctly -> `tests/test_records_model_constants.py` (missing)

#### Rule: Output formats include html, pdf, docx, and others

- `bdd-model-valid-output-formats` Valid output formats include html, pdf, docx, markdown -> `tests/test_records_model_constants.py` (missing)

#### Rule: Record statuses define lifecycle states

- `bdd-model-valid-statuses` Valid statuses include draft, proposed, accepted, deprecated -> `tests/test_records_model_constants.py` (missing)
- `bdd-model-visible-by-default` Visible by default statuses are proposed, accepted, deprecated -> `tests/test_records_model_constants.py` (missing)

#### Rule: Sections define the arc42 document structure

- `bdd-model-section-order` Section order maps all 12 arc42 sections -> `tests/test_records_model_constants.py` (missing)
- `bdd-model-major-section-specs` Major section specs define all 12 sections -> `tests/test_records_model_constants.py` (missing)

### Record templates
- Path: `specs/behavior/features/records/record-templates.feature`
- Summary: Each record type has a Jinja2 template for generating initial content.

#### Rule: All record types have bundled templates

- `bdd-templates-bundled` All record type templates are bundled -> `tests/test_records_record_templates.py` (missing)
- `bdd-templates-registry-covers-all` Registry maps cover all record types -> `tests/test_records_record_templates.py` (missing)
- `bdd-templates-legacy-maps` Legacy maps are preserved for backward compatibility -> `tests/test_records_record_templates.py` (missing)

### Record type registry and normalization
- Path: `specs/behavior/features/records/record-types.feature`
- Summary: Architecture records have typed kinds with aliases, default sections,

#### Rule: All record types are registered with kind, aliases, and defaults

- `bdd-records-types-complete` Registry covers all expected record kinds -> `tests/test_records_record_types.py` (missing)
- `bdd-records-types-aliases` CLI aliases map to canonical kinds -> `tests/test_records_record_types.py` (missing)
- `bdd-records-types-default-section` Each type has a default section -> `tests/test_records_record_types.py` (missing)

#### Rule: Kind normalization resolves aliases and rejects unknowns

- `bdd-records-normalize-alias` Normalize resolves hyphenated alias -> `tests/test_records_record_types.py` (missing)
- `bdd-records-normalize-rejects-unknown` Normalize rejects unknown kind -> `tests/test_records_record_types.py` (missing)

### Record validation
- Path: `specs/behavior/features/records/record-validation.feature`
- Summary: Records are validated for structural correctness: required fields,

#### Rule: Records must have all required fields populated

- `bdd-records-validate-empty-title` Empty title is rejected -> `tests/test_records_record_validation.py` (missing)
- `bdd-records-validate-bad-type` Unknown record type is rejected -> `tests/test_records_record_validation.py` (missing)
- `bdd-records-validate-bad-status` Unknown status is rejected -> `tests/test_records_record_validation.py` (missing)
- `bdd-records-validate-bad-section` Unknown section is rejected -> `tests/test_records_record_validation.py` (missing)

#### Rule: Record ID must match the filename stem

- `bdd-records-validate-id-mismatch` ID-filename mismatch is reported -> `tests/test_records_record_validation.py` (missing)
- `bdd-records-validate-id-format` ID must match configured format pattern -> `tests/test_records_record_validation.py` (missing)

#### Rule: Order must be an integer

- `bdd-records-validate-order-bool` Boolean order is rejected -> `tests/test_records_record_validation.py` (missing)
- `bdd-records-validate-order-string` String order is rejected -> `tests/test_records_record_validation.py` (missing)

### Record visibility filtering
- Path: `specs/behavior/features/records/record-visibility.feature`
- Summary: Records are filtered by status for display in assembled documents.

#### Rule: Visibility depends on status and filter flags

- `bdd-records-visible-proposed` Proposed records are visible by default -> `tests/test_records_record_visibility.py` (missing)
- `bdd-records-visible-accepted` Accepted records are visible by default -> `tests/test_records_record_visibility.py` (missing)
- `bdd-records-visible-draft-hidden` Draft records are hidden unless include_draft is set -> `tests/test_records_record_visibility.py` (missing)
- `bdd-records-visible-draft-shown` Draft records are shown when include_draft is set -> `tests/test_records_record_visibility.py` (missing)
- `bdd-records-visible-superseded-hidden` Superseded records are hidden by default -> `tests/test_records_record_visibility.py` (missing)
- `bdd-records-visible-superseded-shown` Superseded records are shown when include_superseded is set -> `tests/test_records_record_visibility.py` (missing)

## renumber

### ID renumbering
- Path: `specs/behavior/features/renumber/renumber-ids.feature`
- Summary: Renumber changes the ID prefix, width, or segment mode across all

#### Rule: Dry run shows planned changes without mutating

- `bdd-renumber-dry-run` Dry run does not rename files -> `tests/test_renumber_renumber_ids.py` (missing)

#### Rule: Apply renames files and updates frontmatter

- `bdd-renumber-apply-renames` Apply renames record files to new ID format -> `tests/test_renumber_renumber_ids.py` (missing)
- `bdd-renumber-apply-updates-frontmatter` Apply updates the id field in frontmatter -> `tests/test_renumber_renumber_ids.py` (missing)
- `bdd-renumber-apply-updates-references` Apply rewrites references to old IDs in other records -> `tests/test_renumber_renumber_ids.py` (missing)
- `bdd-renumber-apply-updates-config` Apply updates the config with new ID settings -> `tests/test_renumber_renumber_ids.py` (missing)

#### Rule: Invalid records are quarantined during renumber

- `bdd-renumber-quarantine` Records with invalid IDs are quarantined -> `tests/test_renumber_renumber_ids.py` (missing)

## repository

### Archive and doctor repair
- Path: `specs/behavior/features/repository/archive-and-doctor.feature`

#### Rule: Archive moves records out of the live set while preserving numbers

- `bdd-archive-moves-record` Archive moves a record and removes it from normal list output -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-archive-tombstone-validates` Archive tombstones are accepted by check and build -> `tests/test_repository_archive_and_doctor.py` (missing)

#### Rule: Check detects ledger sequence gaps and duplicates

- `bdd-doctor-check-missing-number` Missing ledger number fails check -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-check-duplicate-id` Duplicate ledger IDs fail check -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-check-filename-id-mismatch` Filename and front matter ID must match -> `tests/test_repository_archive_and_doctor.py` (missing)

#### Rule: Doctor repair performs only safe deterministic repairs

- `bdd-doctor-repair-missing-number-tombstone` Repair creates tombstone for a missing ledger number -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-repair-required-section` Repair recreates missing required section files -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-repair-refuses-duplicates` Repair refuses duplicate IDs -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-repair-refuses-manual-segment-change` Repair refuses after manual segment mode change -> `tests/test_repository_archive_and_doctor.py` (missing)
- `bdd-doctor-repair-stale-tombstone-collision` Stale generated tombstone collision is not silently overwritten -> `tests/test_repository_archive_and_doctor.py` (missing)

### Configuration version and path validation
- Path: `specs/behavior/features/repository/config-path-validation.feature`

#### Rule: Versioned configuration fields are parsed explicitly

- `bdd-config-v3-source-extensions` V3 config supports source format extensions -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-v4-source-schema-version` V4 config supports source schema version -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-v5-tracking-settings` V5 config supports tracking settings -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-v6-id-format` V6 config supports ID prefix and width -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-v7-id-segments` V7 config supports ID segment mode and segment map -> `tests/test_repository_config_path_validation.py` (missing)

#### Rule: Configured paths stay within their allowed roots

- `bdd-config-tracking-state-inside-archledger-dir` Tracking state file must stay inside the archledger directory -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-build-output-dir-inside-workspace` Build output dir must stay inside workspace root -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-build-default-output-inside-output-dir` Build default output must stay inside output dir -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-build-output-dir-relative-root` Build output dir is relative to workspace root -> `tests/test_repository_config_path_validation.py` (missing)

#### Rule: Build output entries are validated before use

- `bdd-config-default-output-extension-matches-format` Default output extension must match default format -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-build-outputs-reject-unknown-format` Build outputs reject unknown formats -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-build-outputs-validate-settings` Per-output build settings are validated -> `tests/test_repository_config_path_validation.py` (missing)

#### Rule: Ambiguous config values are rejected

- `bdd-config-version-bool-rejected` Boolean config version is rejected -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-integer-bool-rejected` Boolean integer-like fields are rejected -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-kroki-renderer-rejected` Unsupported Kroki renderer is rejected -> `tests/test_repository_config_path_validation.py` (missing)
- `bdd-config-invalid-segment-value-rejected` Invalid ID segment values are rejected -> `tests/test_repository_config_path_validation.py` (missing)

### Profile management
- Path: `specs/behavior/features/repository/profile-management.feature`

#### Rule: Profile migration moves legacy sections and updates config

- `bdd-profile-migrate-legacy-sections` Legacy sections are moved into arc42 profile directory -> `tests/test_repository_profile_management.py` (missing)

#### Rule: BDD is not a standalone profile

- `bdd-profile-enable-bdd-explains-metadata-layer` Enabling BDD as a profile explains the model -> `tests/test_repository_profile_management.py` (missing)
- `bdd-profile-disable-bdd-explains-metadata-layer` Disabling BDD as a profile explains the model -> `tests/test_repository_profile_management.py` (missing)

#### Rule: SDD profile changes preserve policy

- `bdd-profile-enable-sdd-preserves-policy` Enabling SDD preserves existing SDD policy -> `tests/test_repository_profile_management.py` (missing)

### Record creation command behavior
- Path: `specs/behavior/features/repository/record-creation.feature`

#### Rule: New command creates records in the correct type directories

- `bdd-new-requirement-record` Requirement record is created with requirement template -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-black-box-record` Black box record is created in building blocks -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-white-box-record` White box record is created in building blocks -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-adr-legacy-alias` ADR alias creates an architecture decision record -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-strategy-item-record` Strategy item record is created -> `tests/test_repository_record_creation.py` (missing)

#### Rule: Type-specific options populate front matter

- `bdd-new-context-interface-partner` Context interface accepts context kind and partner -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-infrastructure-environment` Infrastructure accepts environment -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-quality-scenario-quality-environment` Quality scenario accepts quality and environment -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-diagram-options` Diagram creation accepts diagram options -> `tests/test_repository_record_creation.py` (missing)

#### Rule: Creation uses configured ID format and never reuses archived numbers

- `bdd-new-configured-id-format` Configured ID prefix and width are applied -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-segment-mode-type` Type segment mode adds record type segment -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-custom-record-extension` Custom record extension increments correctly -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-does-not-reuse-archived-number` Archived numbers are not reused -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-refuses-when-counter-proves-missing-number` New refuses allocation when storage counter proves a gap -> `tests/test_repository_record_creation.py` (missing)

#### Rule: Creation and seeding expose stable automation output

- `bdd-new-json-output` New command returns JSON payload -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-diagram-json-output` New diagram JSON includes diagram metadata -> `tests/test_repository_record_creation.py` (missing)
- `bdd-seed-arc42-minimal` Arc42 minimal seed creates starter records -> `tests/test_repository_record_creation.py` (missing)
- `bdd-new-every-record-type` Every registered record type can be created -> `tests/test_repository_record_creation.py` (missing)

### Repository check and validation
- Path: `specs/behavior/features/repository/repository-check.feature`
- Summary: The check command validates all records for structural issues, content

#### Rule: Check reports errors and warnings for invalid records

- `bdd-repo-check-passes` Valid workspace passes check -> `tests/test_repository_repository_check.py` (missing)
- `bdd-repo-check-archive-tombstones` Archive tombstones are accepted without errors -> `tests/test_repository_repository_check.py` (missing)
- `bdd-repo-check-canonical-config` Canonical config wins when both exist -> `tests/test_repository_repository_check.py` (missing)

#### Rule: Snapshot captures source state for change tracking

- `bdd-repo-snapshot-creates-state` Snapshot writes source-state JSON -> `tests/test_repository_repository_check.py` (missing)
- `bdd-repo-snapshot-respects-disabled` Snapshot is skipped when tracking is disabled -> `tests/test_repository_repository_check.py` (missing)

### Repository configuration round-trip
- Path: `specs/behavior/features/repository/repository-config.feature`
- Summary: Project configuration is loaded, validated, and rendered back to TOML

#### Rule: Config round-trip preserves all settings

- `bdd-config-roundtrip-markdown` Default markdown config round-trips correctly -> `tests/test_repository_repository_config.py` (missing)
- `bdd-config-roundtrip-asciidoc` Default asciidoc config round-trips correctly -> `tests/test_repository_repository_config.py` (missing)

#### Rule: V2 config supports new build and skill keys

- `bdd-config-v2-build-keys` V2 config supports build_arc42 settings -> `tests/test_repository_repository_config.py` (missing)
- `bdd-config-v2-skill-keys` V2 config supports skill file settings -> `tests/test_repository_repository_config.py` (missing)

#### Rule: Archledger directory path is resolved correctly

- `bdd-config-relative-dir` Relative archledger dir is resolved to config path -> `tests/test_repository_repository_config.py` (missing)

### Repository initialization
- Path: `specs/behavior/features/repository/repository-init.feature`
- Summary: New archledger workspaces are initialized with config, storage metadata,

#### Rule: Init creates the canonical workspace structure

- `bdd-repo-init-creates-config` Init writes archledger.toml config file -> `tests/test_repository_repository_init.py` (missing)
- `bdd-repo-init-creates-storage-meta` Init creates storage metadata -> `tests/test_repository_repository_init.py` (missing)
- `bdd-repo-init-creates-sections` Init creates all arc42 section directories -> `tests/test_repository_repository_init.py` (missing)
- `bdd-repo-init-creates-record-dirs` Init creates directories for all record types -> `tests/test_repository_repository_init.py` (missing)
- `bdd-repo-init-project-name-default` Project name defaults to workspace basename -> `tests/test_repository_repository_init.py` (missing)

#### Rule: Status reports workspace health

- `bdd-repo-status-counts` Status counts sections and record directories -> `tests/test_repository_repository_init.py` (missing)

### Repository mutation CLI
- Path: `specs/behavior/features/repository/repository-mutation.feature`
- Summary: The mutation CLI provides commands for updating individual record

#### Rule: Nested mutation commands target specific fields

- `bdd-mutation-cli-status` Status command updates record status -> `tests/test_repository_repository_mutation.py` (missing)
- `bdd-mutation-cli-meta` Meta command sets arbitrary metadata -> `tests/test_repository_repository_mutation.py` (missing)

#### Rule: Body commands modify record content

- `bdd-mutation-cli-body-set` Body set command replaces record body -> `tests/test_repository_repository_mutation.py` (missing)
- `bdd-mutation-cli-body-append` Body append command adds to record body -> `tests/test_repository_repository_mutation.py` (missing)

### Repository read operations
- Path: `specs/behavior/features/repository/repository-read.feature`
- Summary: Records can be read as JSON with optional body inclusion and status

#### Rule: Read returns records in JSON format

- `bdd-repo-read-json-body` Read JSON includes record bodies when requested -> `tests/test_repository_repository_read.py` (missing)
- `bdd-repo-read-json-draft` Read JSON includes draft records when flag is set -> `tests/test_repository_repository_read.py` (missing)
- `bdd-repo-read-json-excludes-draft` Read JSON excludes draft records by default -> `tests/test_repository_repository_read.py` (missing)

### JSON schema installation
- Path: `specs/behavior/features/repository/repository-schemas.feature`
- Summary: JSON schemas can be installed to external locations for tooling

#### Rule: Schema install writes schema files to target directory

- `bdd-schema-install-jsonschema` Install returns the target path for jsonschema -> `tests/test_repository_repository_schemas.py` (missing)
- `bdd-schema-install-legacy-refuses-overwrite` Install refuses to overwrite without force flag -> `tests/test_repository_repository_schemas.py` (missing)
- `bdd-schema-install-force-overwrite` Install overwrites with force flag -> `tests/test_repository_repository_schemas.py` (missing)

### JSON schema and CLI payload contracts
- Path: `specs/behavior/features/repository/schema-json-contracts.feature`

#### Rule: Schema command lists supported schema contracts

- `bdd-schema-json-lists-contracts` Schema JSON lists record types, statuses, sections, and formats -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-jsonschema-target-returned` JSON schema install reports target path -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-install-refuses-overwrite` Schema install refuses overwrite without force -> `tests/test_repository_schema_json_contracts.py` (missing)

#### Rule: Core CLI JSON responses retain stable shapes

- `bdd-json-status-shape` Status JSON shape is stable -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-json-check-shape` Check JSON shape is stable -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-json-paths-shape` Paths JSON shape includes archive and source state paths -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-json-missing-record-error` Missing record returns structured JSON error -> `tests/test_repository_schema_json_contracts.py` (missing)

#### Rule: Feature-specific JSON payloads match bundled schemas

- `bdd-schema-sdd-check-v2` SDD check payload matches bundled schema -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-bdd-export` BDD export payload matches bundled schema -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-bdd-sync` BDD sync payload matches bundled schema -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-sdd-init` SDD init payload matches bundled schema -> `tests/test_repository_schema_json_contracts.py` (missing)
- `bdd-schema-sdd-explain` SDD explain payload matches bundled schema -> `tests/test_repository_schema_json_contracts.py` (missing)

### Skill file generation
- Path: `specs/behavior/features/repository/skill-file.feature`
- Summary: The skill file provides agent instructions for working with archledger

#### Rule: Skill file exists and is valid

- `bdd-skill-file-exists` Skill file is present in the project -> `tests/test_repository_skill_file.py` (missing)
- `bdd-skill-file-mentions-formats` Skill file mentions supported formats -> `tests/test_repository_skill_file.py` (missing)
- `bdd-skill-file-instructs-read` Skill file instructs reading without export -> `tests/test_repository_skill_file.py` (missing)
- `bdd-skill-file-no-legacy-markdown` Skill file does not reference legacy markdown export -> `tests/test_repository_skill_file.py` (missing)

## scopes

### Record scope normalization and matching
- Path: `specs/behavior/features/scopes/record-scope.feature`
- Summary: Scope declares which addon, addon group, integration, subsystem, or

#### Rule: Scope is normalized from front-matter metadata

- `bdd-scope-normalize-valid` Valid scope is normalized without errors -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-invalid-kind` Invalid scope kind is rejected -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-missing-name` Missing scope name is rejected -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-empty-applies-to` Empty applies_to is rejected -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-lifecycle` Valid lifecycle values are accepted -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-invalid-lifecycle` Invalid lifecycle is rejected -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-normalize-none` None scope returns None without errors -> `tests/test_scopes_record_scope.py` (missing)

#### Rule: Scope matching determines if a path falls within scope

- `bdd-scope-matches-directory` Path under applies_to directory matches -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-matches-exact-file` Exact file path matches -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-excludes-path` Excluded path does not match -> `tests/test_scopes_record_scope.py` (missing)
- `bdd-scope-no-match` Path outside scope does not match -> `tests/test_scopes_record_scope.py` (missing)

## sdd

### SDD-BDD integration
- Path: `specs/behavior/features/sdd/sdd-bdd-integration.feature`
- Summary: The SDD check validates BDD metadata shape and automation status

#### Rule: SDD validates BDD metadata structure

- `bdd-sdd-bdd-shape-valid` Valid BDD metadata passes SDD shape check -> `tests/test_sdd_sdd_bdd_integration.py` (missing)
- `bdd-sdd-bdd-shape-invalid` Structurally invalid BDD metadata fails SDD check -> `tests/test_sdd_sdd_bdd_integration.py` (missing)

#### Rule: Deprecated BDD feature paths are detected

- `bdd-sdd-deprecated-feature-path` Records with deprecated feature paths get a warning -> `tests/test_sdd_sdd_bdd_integration.py` (missing)

### SDD lifecycle commands
- Path: `specs/behavior/features/sdd/sdd-lifecycle-commands.feature`

#### Rule: SDD init and status expose enabled contract state

- `bdd-sdd-init-enables-profile` SDD init enables the profile and writes policy -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-init-strict-seed` Strict SDD init can seed minimal contract records -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-init-dry-run` SDD init dry run reports changes without writing -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-status-json-policy` SDD status reports policy and enabled profiles -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)

#### Rule: Policy commands show and change effective settings

- `bdd-sdd-policy-show` Policy show reports effective policy -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-policy-set-updates-config` Policy set updates the SDD policy block -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-policy-set-requires-flag` Policy set requires at least one flag -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)

#### Rule: Rule explanation and waivers are explicit and reversible

- `bdd-sdd-explain-single-rule` Explain single SDD rule -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-explain-all-rules` Explain all SDD rules -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-explain-unknown-rule` Unknown SDD rule code fails clearly -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-waive-add-requires-reason` Adding waiver requires a reason -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-waive-add-suppresses-rule` Waiver suppresses matching rule -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-waive-remove-restores-rule` Removing waiver restores finding -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-waive-unknown-rule-rejected` Waiver rejects unknown rule code -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)

#### Rule: Coverage and scoped checks expose gaps without scanning unrelated records

- `bdd-sdd-coverage-gaps` Coverage reports dimensions and gaps -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-coverage-include-bdd` Coverage can include BDD dimensions -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-coverage-by-record` Coverage by record lists per-record detail -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-check-scoped-record` SDD check can target one record -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)
- `bdd-sdd-check-scoped-kind` SDD check can target one kind -> `tests/test_sdd_sdd_lifecycle_commands.py` (missing)

### SDD traceability policy engine
- Path: `specs/behavior/features/sdd/sdd-policy.feature`
- Summary: The SDD policy engine evaluates traceability contracts on loaded records,

#### Rule: SDD options are resolved from config and CLI overrides

- `bdd-sdd-options-from-config` Config provides default SDD options -> `tests/test_sdd_sdd_policy.py` (missing)
- `bdd-sdd-options-cli-override` CLI override wins over config default -> `tests/test_sdd_sdd_policy.py` (missing)

#### Rule: SDD check enforces traceability contracts

- `bdd-sdd-check-passes` Records meeting all contracts pass SDD check -> `tests/test_sdd_sdd_policy.py` (missing)
- `bdd-sdd-check-missing-ac` Accepted record without acceptance criteria is flagged -> `tests/test_sdd_sdd_policy.py` (missing)
- `bdd-sdd-check-missing-test-refs` Accepted record without test refs is flagged -> `tests/test_sdd_sdd_policy.py` (missing)
- `bdd-sdd-check-missing-implementation` Accepted record without source refs is flagged -> `tests/test_sdd_sdd_policy.py` (missing)
- `bdd-sdd-check-placeholder-body` Accepted record with placeholder body is flagged -> `tests/test_sdd_sdd_policy.py` (missing)

#### Rule: Behavior records require BDD Given/When/Then

- `bdd-sdd-check-bdd-gwt` Behavior record without BDD metadata is flagged -> `tests/test_sdd_sdd_policy.py` (missing)

#### Rule: PR check validates changed files against records

- `bdd-sdd-pr-unlinked-file` Changed file not linked to any record is flagged -> `tests/test_sdd_sdd_policy.py` (missing)

## source-refs

### Source reference normalization
- Path: `specs/behavior/features/source-refs/source-references.feature`
- Summary: Source refs link records to implementation files with optional symbols

#### Rule: Source refs are normalized and validated

- `bdd-source-refs-normalize-valid` Valid source ref is normalized -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-invalid-path` Non-POSIX path is rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-absolute-path` Absolute path is rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-dotdot-path` Path with .. is rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-invalid-role` Invalid role is rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-none` None source refs returns empty tuple -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-normalize-missing-file` Missing file produces a warning -> `tests/test_source_refs_source_references.py` (missing)

#### Rule: Relative POSIX path validation catches common errors

- `bdd-source-refs-validate-posix` Backslash separators are rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-validate-relative` Absolute paths are rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-validate-dotdot` Parent traversal is rejected -> `tests/test_source_refs_source_references.py` (missing)
- `bdd-source-refs-validate-empty` Empty path is rejected -> `tests/test_source_refs_source_references.py` (missing)

## source-tracking

### Source scanning and impact resolution
- Path: `specs/behavior/features/source-tracking/source-scan-and-impact.feature`

#### Rule: Workspace scan excludes state, build, and oversized files

- `bdd-source-scan-excludes-archledger-state` Workspace scan excludes archledger state and build output -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)
- `bdd-source-scan-root-build-dir-not-skipped` Root build directory does not hide the whole workspace -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)

#### Rule: Source hashes are stable for text content

- `bdd-source-hash-normalizes-line-endings` Source hash normalizes line endings -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)
- `bdd-source-state-sha256-only` Source state JSON stores hashes without size or timestamps -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)

#### Rule: Source state parser rejects unsafe or obsolete state files

- `bdd-source-state-v1-rejected` Source state v1 is rejected -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)
- `bdd-source-state-backslash-path-rejected` Backslash paths are rejected in source state -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)

#### Rule: Changed files resolve to records and unlinked files

- `bdd-source-impact-linked-records` Changed source ref resolves impacted records -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)
- `bdd-source-impact-unlinked-files` Changed unlinked files are reported separately -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)
- `bdd-source-changed-json-impacted-record` Changed JSON reports modified file and impacted record -> `tests/test_source_tracking_source_scan_and_impact.py` (missing)

### Source state tracking and change detection
- Path: `specs/behavior/features/source-tracking/source-state.feature`
- Summary: Source tracking captures file hashes for change detection between

#### Rule: Source state records file and directory hashes

- `bdd-source-state-roundtrip` Source state serializes and deserializes correctly -> `tests/test_source_tracking_source_state.py` (missing)
- `bdd-source-state-relative-paths` Source state uses relative paths -> `tests/test_source_tracking_source_state.py` (missing)
- `bdd-source-state-schema` Source state JSON uses correct schema -> `tests/test_source_tracking_source_state.py` (missing)

#### Rule: Changeset detects added, modified, and deleted files

- `bdd-changeset-detects-added` New files are detected as added -> `tests/test_source_tracking_source_state.py` (missing)
- `bdd-changeset-detects-modified` Changed files are detected as modified -> `tests/test_source_tracking_source_state.py` (missing)
- `bdd-changeset-detects-deleted` Removed files are detected as deleted -> `tests/test_source_tracking_source_state.py` (missing)
- `bdd-changeset-impacted-records` Changeset identifies impacted records -> `tests/test_source_tracking_source_state.py` (missing)

## storage

### Front matter and storage primitives
- Path: `specs/behavior/features/storage/frontmatter-and-storage.feature`

#### Rule: Front matter documents round-trip across supported source formats

- `bdd-frontmatter-read-markdown-valid` Markdown front matter document is read correctly -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-frontmatter-write-markdown-roundtrip` Markdown front matter document writes and reads back -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-frontmatter-read-asciidoc-valid` AsciiDoc front matter document is accepted -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-frontmatter-write-asciidoc-roundtrip` AsciiDoc front matter document writes and reads back -> `tests/test_storage_frontmatter_and_storage.py` (missing)

#### Rule: Invalid front matter fails clearly

- `bdd-frontmatter-missing-rejected` Missing front matter is rejected -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-frontmatter-non-mapping-rejected` Non-mapping YAML front matter is rejected -> `tests/test_storage_frontmatter_and_storage.py` (missing)

#### Rule: Source file iteration respects configured extensions

- `bdd-storage-iter-source-files-extension-filter` Source file iteration filters by extension -> `tests/test_storage_frontmatter_and_storage.py` (missing)

#### Rule: Storage metadata preserves counter floors and rejects boolean integers

- `bdd-storage-meta-version-two-required` Storage metadata must use schema version 2 -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-storage-meta-next-number-bool-rejected` Boolean next number is rejected -> `tests/test_storage_frontmatter_and_storage.py` (missing)
- `bdd-storage-meta-counter-floor-preserved` Counter recomputation preserves the existing floor -> `tests/test_storage_frontmatter_and_storage.py` (missing)

#### Rule: Atomic writes replace contents without leaving temporary files

- `bdd-storage-atomic-write-cleanup` Atomic write leaves no temporary files behind -> `tests/test_storage_frontmatter_and_storage.py` (missing)

## test-refs

### Test reference normalization
- Path: `specs/behavior/features/test-refs/test-references.feature`
- Summary: Test refs link records to executable test files or test node IDs.

#### Rule: Test refs are normalized from front-matter metadata

- `bdd-test-refs-normalize-compact` Compact string form is parsed correctly -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-dict` Dict form is normalized correctly -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-invalid-path` Non-POSIX path is rejected -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-missing-file` Missing test file produces a warning -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-none` None test refs returns empty tuple -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-empty-entry` Empty string entry is rejected -> `tests/test_test_refs_test_references.py` (missing)
- `bdd-test-refs-normalize-role` Test ref role is preserved -> `tests/test_test_refs_test_references.py` (missing)

## trace

### Record tracing
- Path: `specs/behavior/features/trace/record-trace.feature`
- Summary: Trace answers: What requirement is this implementing? Which ADR constrains

#### Rule: Trace walks links in both directions and categorizes results

- `bdd-trace-outgoing-links` Trace includes outgoing linked records -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-incoming-links` Trace includes incoming linked records -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-categorizes-types` Trace categorizes records by type -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-source-refs` Trace includes source references -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-test-refs` Trace includes test references -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-not-found` Trace reports error for missing record -> `tests/test_trace_record_trace.py` (missing)
- `bdd-trace-schema` Trace output uses archledger.trace.v1 schema -> `tests/test_trace_record_trace.py` (missing)

#### Rule: Combo trace extracts task, AC, and BDD IDs from trace data

- `bdd-combo-trace-extracts-ids` Combo trace finds task, AC, and BDD IDs -> `tests/test_trace_record_trace.py` (missing)
- `bdd-combo-trace-empty-for-missing` Combo trace returns empty arrays for missing fields -> `tests/test_trace_record_trace.py` (missing)
- `bdd-combo-trace-schema` Combo trace uses combi.trace.v1 schema -> `tests/test_trace_record_trace.py` (missing)
