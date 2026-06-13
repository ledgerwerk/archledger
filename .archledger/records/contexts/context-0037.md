---
id: context-0037
type: context_interface
title: CI pipeline
schema_version: 2
date: "2026-05-22"
body_format: markdown
status: accepted
section: context_and_scope
order: 30
context_kind: technical
partner: CI runner
inputs:
  - archledger check result
  - archledger build output
outputs:
  - CI pass/fail signal
  - Published architecture document artifact
channels:
  - Process exit codes
  - Build artifact storage
source_refs:
  - .github/workflows/tests.yml
  - .github/workflows/codecov.yml
  - .github/workflows/pre-commit.yml
  - tests/test_build.py
kind: context
---

A CI runner can execute `archledger check` to validate record integrity and `archledger build` to produce the rendered document. Non-zero exit codes signal validation failures. The built Markdown can be published as a CI artifact or deployed to a documentation site. The project uses GitHub Actions for CI (`.github/workflows/tests.yml` for test execution, `.github/workflows/codecov.yml` for coverage reporting, `.github/workflows/pre-commit.yml` for linting, and `.github/workflows/python-publish.yml` for PyPI releases).
