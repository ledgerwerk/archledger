---
id: glossary_0007
type: glossary_term
title: "Source State"
status: accepted
section: glossary
order: 70
term: "Source State"
definition: "A persisted snapshot of all tracked workspace files with their SHA-256 hashes, sizes, and modification times. Used as the baseline for change detection."
---

A persisted snapshot of all tracked workspace files with their SHA-256 hashes, sizes, and modification times. Created by `archledger snapshot` and used by `archledger changed` as the baseline for change detection. Stored as JSON in the build directory.
