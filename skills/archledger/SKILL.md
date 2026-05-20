---
name: archledger
description: Fill and maintain AsciiDoc-backed arc42 architecture documentation with YAML front matter, explicit migration, validation, and multi-format builds.
license: Apache-2.0
compatibility: opencode,codex,chatgpt
metadata: architecture-documentation,arc42,coding-agents
---

# archledger skill

## When to use this skill

Use this skill when a coding agent needs to create, enrich, repair, migrate, or build architecture documentation for a software repository with `archledger`. The target output is a complete arc42-style architecture artifact assembled from human-editable source fragments whose canonical format is YAML front matter plus AsciiDoc body content.

Typical triggers:

- The user asks for architecture documentation, arc42, ADRs, building block views, context views, quality scenarios, risks, or glossary entries.
- The repository contains `archledger.toml`, `.archledger.toml`, `.archledger/`, or an external configured `archledger_dir`.
- The user asks an agent to fill architecture documentation from code, tests, README files, package metadata, deployment files, or existing design notes.

## Never do these things

- Do not edit generated build output as the canonical source. Update section files and record files instead.
- Do not leave placeholder bodies in accepted records.
- Do not invent external systems, compliance constraints, stakeholders, or production deployments without evidence. Mark uncertain items as `draft` or `proposed` and record the assumption in the body.
- Do not treat every source file as a building block. Prefer architecturally relevant modules, boundaries, interfaces, runtime flows, and decisions.
- Do not bypass `archledger check` before a build.
- Do not delete existing records just because they look stale. Deprecate or supersede them unless the user explicitly requests deletion.
- Do not commit `.archledger/` by default. The project config is the commit-safe source pointer; the storage directory may be ignored or external.

## Fresh-context entry protocol

1. Locate the project root and config.

   ```bash
   archledger --json where
   archledger --json status
   ```

2. Inspect current records.

   ```bash
   archledger --json list --include-draft
   archledger --json check
   ```

3. If storage is missing, initialize it only when the user asked to create architecture documentation for this workspace.

   ```bash
   archledger init
   ```

4. If the user wants a starter set, bootstrap it explicitly:

   ```bash
   archledger seed arc42-minimal
   ```

5. Inspect repository evidence before writing content. Use README, package metadata, source tree, tests, deployment files, CI, docs, and existing ADRs/design notes.

6. Create or update records in small batches. Prefer accepted records only when the evidence is strong; use proposed/draft for assumptions.

7. Run validation and build.

   ```bash
   archledger check
   archledger build --format asciidoc
   ```

## Minimum arc42 fill set

A useful first artifact should contain at least:

1. Introduction and Goals
   - Requirement records plus short section prose.
   - Three to five quality goals with concrete scenarios.
   - Stakeholders and expectations.
2. Architecture Constraints
   - Technical, organizational, regulatory, and convention constraints.
3. Context and Scope
   - Business context partners and domain input/output.
   - Technical context channels/protocols and input/output mapping.
4. Solution Strategy
   - Section prose plus strategy items that connect drivers, constraints, and ADRs.
5. Building Block View
   - One white box for the overall system.
   - Architecturally relevant black boxes.
   - Important interfaces.
6. Runtime View
   - Representative scenarios: primary happy path, critical error path, startup/build path, or sync/import/export path.
7. Deployment View
   - Development, local, CI, and production assumptions only when supported by evidence.
8. Cross-cutting Concepts
   - Only concepts that actually matter for this system, such as configuration, storage, validation, rendering, versioning, security, logging, or error handling.
9. Architecture Decisions
   - ADRs for decisions with persistent consequences.
10. Quality Requirements

    - Quality requirement overview records plus detailed quality scenarios with source, stimulus, environment, artifact, response, and response measure.

11. Risks and Technical Debt

   - Risks with severity, probability, mitigation, and evidence.

12. Glossary

   - Domain and technical terms needed by stakeholders.

## Record authoring protocol

Use the CLI to allocate ids and paths, then edit the generated `.adoc` source fragment.

```bash
archledger new requirement --title "Render architecture document from AsciiDoc records" --status proposed
archledger new white-box --title "Overall System" --status proposed
archledger new black-box --title "CLI" --parent white_box_0001 --status proposed
archledger new strategy-item --title "Keep records as canonical source" --status proposed
archledger new adr --title "Use AsciiDoc fragments with YAML front matter" --status proposed
archledger new quality-requirement --title "Deterministic builds" --status proposed
archledger new context-interface --title "GitHub" --context-kind business --partner GitHub --status proposed
archledger new infrastructure --title "Local CLI runtime" --environment development --status proposed
archledger new quality-scenario --title "Deterministic build" --quality reproducibility --environment ci --status proposed
```

Every record must keep YAML front matter at the top, delimited by `---`, followed by rich AsciiDoc. Treat front matter as machine-readable indexing data and the AsciiDoc body as the human architecture explanation.

Common fields:

```yaml
schema_version: 2
id: black_box_0001
type: black_box
title: "CLI"
status: proposed
section: building_block_view
order: 10
parent: white_box_0001
level: 1
body_format: asciidoc
tags: []
created_at: "2026-05-19T00:00:00Z"
updated_at: "2026-05-19T00:00:00Z"
```

Status rules:

- `draft`: incomplete, not included by default.
- `proposed`: usable but not formally accepted.
- `accepted`: confirmed and included by default.
- `deprecated`: still visible by default, but no longer preferred.
- `superseded`: hidden unless explicitly included.

## Evidence rules for filling content

When deriving architecture from code:

- Use import boundaries and package layout to suggest building blocks.
- Use CLI commands, public APIs, and storage adapters as interfaces.
- Use tests to infer supported behavior and acceptance rules.
- Use configuration files for constraints and deployment assumptions.
- Use README/docs for user-facing goals and workflow claims.
- Use error classes and validation logic to identify risks, quality requirements, and operational behavior.

Mark assumptions explicitly:

```adoc
[discrete]
=== Evidence

- `pyproject.toml` declares the `archledger` console script.
- `archledger/assembly.py` assembles the canonical architecture document.

[discrete]
=== Assumptions

- Production usage is local CLI execution until deployment evidence exists.
```

## Validation protocol

Before finalizing:

```bash
archledger check
archledger build --format asciidoc
archledger build --format html
python -m pytest -q
```

For automation, prefer JSON:

```bash
archledger --json check
archledger --json build --formats html,markdown
```

A record is not done until:

- Its body is not placeholder text.
- Required front matter is valid.
- Parent references resolve.
- The record is in the correct arc42 section.
- `archledger check` has no errors.
- Strict warnings are either fixed or intentionally left as proposed/draft work.

## Migration and export rules

- Treat Markdown source projects as legacy inputs. Use `archledger convert-sources --to asciidoc --write` before expecting canonical AsciiDoc assembly or export formats.
- Do not hand-edit generated `.archledger/build/*` outputs.
- `archledger build --format asciidoc` is the dependency-free canonical build for AsciiDoc-backed projects.
- HTML export requires `asciidoctor`.
- PDF export requires `asciidoctor-pdf`.
- DOCX, Markdown, reStructuredText, and Textile export require `pandoc`.

## Content quality bar

Good archledger content is concrete, traceable, and concise. Each item should answer:

- What exists?
- Why does it exist?
- Which source evidence supports it?
- Which stakeholder cares?
- Which quality goal, constraint, decision, or risk does it affect?

Avoid generic architecture filler. Prefer one precise paragraph over a broad
buzzword list.
