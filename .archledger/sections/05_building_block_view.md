---
id: section_building_block_view
type: section
section: building_block_view
title: Building Block View
order: 50
status: accepted
---

The system is decomposed into eight black boxes within a single white box. The CLI Layer receives user input, delegates to the Repository Layer for business logic, which in turn uses the Model Layer for data structures and validation, the Storage Layer for file I/O, the Assembly Layer for document assembly, the Dialect Layer for format-aware rendering, the Section Rendering Layer for per-record-type output, the Converter Layer for multi-format export, and the Source Tracking Layer for change detection and impact analysis.
