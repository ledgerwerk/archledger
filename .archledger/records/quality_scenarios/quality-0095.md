---
schema_version: 2
id: quality-0095
type: quality_scenario
title: Missing converter fails clearly
status: accepted
section: quality_requirements
order: 40
date: "2026-05-21"
quality: operability
source: build command + converter detection
stimulus: User requests PDF/DOCX without required converter installed.
environment: normal_development
artifact: conversion stage
response: Build fails with explicit missing tool and install hint.
response_measure: Exit code non-zero with actionable diagnostic.
body_format: markdown
created_at: "2026-05-21T18:18:54Z"
updated_at: "2026-05-21T18:18:54Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
---

Missing converters fail clearly and point to installation guidance.
