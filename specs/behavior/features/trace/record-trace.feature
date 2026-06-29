@area-trace @feature-record-trace
Feature: Record tracing

  Trace answers: What requirement is this implementing? Which ADR constrains
  it? Which files implement it? Which tests validate it? Which risks remain
  open?

  @rule-trace
  Rule: Trace walks links in both directions and categorizes results

    @bdd-trace-outgoing-links
    @req-REQ-0020
    @ac-AC-0282
    Example: Trace includes outgoing linked records
      Given a record with a "satisfies" link to a requirement
      When build_trace is called
      Then the requirement appears in the trace requirements list

    @bdd-trace-incoming-links
    @req-REQ-0020
    @ac-AC-0283
    Example: Trace includes incoming linked records
      Given a record that is linked by another record
      When build_trace is called
      Then the linking record appears in incoming_links

    @bdd-trace-categorizes-types
    @req-REQ-0020
    @ac-AC-0284
    Example: Trace categorizes records by type
      Given linked records of types requirement, adr, constraint, risk
      When build_trace is called
      Then each record appears in its correct category

    @bdd-trace-source-refs
    @req-REQ-0020
    @ac-AC-0285
    Example: Trace includes source references
      Given a record with source_refs
      When build_trace is called
      Then source_refs appear in the trace output

    @bdd-trace-test-refs
    @req-REQ-0020
    @ac-AC-0286
    Example: Trace includes test references
      Given a record with test_refs
      When build_trace is called
      Then test_refs appear in the trace output

    @bdd-trace-not-found
    @req-REQ-0020
    @ac-AC-0287
    Example: Trace reports error for missing record
      Given no record with id "al_9999"
      When build_trace is called with "al_9999"
      Then the trace contains error "Record not found"

    @bdd-trace-schema
    @req-REQ-0020
    @ac-AC-0288
    Example: Trace output uses archledger.trace.v1 schema
      Given any valid record
      When build_trace is called
      Then the response schema is "archledger.trace.v1"

  @rule-combo-trace
  Rule: Combo trace extracts task, AC, and BDD IDs from trace data

    @bdd-combo-trace-extracts-ids
    @req-REQ-0020
    @ac-AC-0289
    Example: Combo trace finds task, AC, and BDD IDs
      Given a trace payload containing task-0001, ac-0002, bdd-0003
      When build_combo_trace is called
      Then task_ids contains "task-0001"
      And ac_ids contains "ac-0002"
      And bdd_ids contains "bdd-0003"

    @bdd-combo-trace-empty-for-missing
    @req-REQ-0020
    @ac-AC-0290
    Example: Combo trace returns empty arrays for missing fields
      Given a trace payload with no IDs
      When build_combo_trace is called
      Then task_ids, ac_ids, bdd_ids are all empty

    @bdd-combo-trace-schema
    @req-REQ-0020
    @ac-AC-0291
    Example: Combo trace uses combi.trace.v1 schema
      Given any trace payload
      When build_combo_trace is called
      Then the response schema is "combi.trace.v1"
