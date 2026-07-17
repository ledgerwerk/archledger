---
schema_version: 4
id: quality-0095
type: quality_scenario
title: Missing converter fails clearly
status: accepted
section: quality_requirements
order: 40
quality: operability
source: build command + converter detection
stimulus: User requests PDF/DOCX without required converter installed.
environment: normal_development
artifact: conversion stage
response: Build fails with explicit missing tool and install hint.
response_measure: Exit code non-zero with actionable diagnostic.
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Missing converters fail clearly and point to installation guidance.
