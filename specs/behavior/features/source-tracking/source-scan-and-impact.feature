@area-source-tracking @feature-source-scan-and-impact
Feature: Source scanning and impact resolution

  # Source tracking should hash normalized source content, exclude generated or
  # state directories, reject obsolete state schemas, and resolve changed files
  # back to records and sections.

  @rule-scanning
  Rule: Workspace scan excludes state, build, and oversized files

    @bdd-source-scan-excludes-archledger-state
    @req-REQ-0017
    @ac-AC-0248
    Example: Workspace scan excludes archledger state and build output
      Given a workspace containing source files, .archledger state, and build output
      When the workspace is scanned for source state
      Then generated state and build files are excluded
      And source files remain included

    @bdd-source-scan-root-build-dir-not-skipped
    @req-REQ-0017
    @ac-AC-0249
    Example: Root build directory does not hide the whole workspace
      Given a workspace whose configured build output directory is the root
      When source snapshot is created
      Then normal source files are still scanned

  @rule-hashing
  Rule: Source hashes are stable for text content

    @bdd-source-hash-normalizes-line-endings
    @req-REQ-0017
    @ac-AC-0250
    Example: Source hash normalizes line endings
      Given two text files with the same content and different line endings
      When source hashes are computed
      Then the files have the same sha256 hash

    @bdd-source-state-sha256-only
    @req-REQ-0017
    @ac-AC-0251
    Example: Source state JSON stores hashes without size or timestamps
      Given a source state snapshot
      When it is serialized to JSON
      Then tracked file entries contain sha256
      And tracked file entries do not contain size or modification time

  @rule-state-validation
  Rule: Source state parser rejects unsafe or obsolete state files

    @bdd-source-state-v1-rejected
    @req-REQ-0017
    @ac-AC-0252
    Example: Source state v1 is rejected
      Given a source-state JSON file with schema version v1
      When the source state is read
      Then a source state error is raised

    @bdd-source-state-backslash-path-rejected
    @req-REQ-0017
    @ac-AC-0253
    Example: Backslash paths are rejected in source state
      Given a source-state JSON file containing a path with backslashes
      When the source state is read
      Then a source state error is raised

  @rule-impact
  Rule: Changed files resolve to records and unlinked files

    @bdd-source-impact-linked-records
    @req-REQ-0017
    @ac-AC-0254
    Example: Changed source ref resolves impacted records
      Given a changed file referenced by an accepted record
      When source impact is resolved
      Then the record is listed as impacted
      And matching source_refs are reported

    @bdd-source-impact-unlinked-files
    @req-REQ-0017
    @ac-AC-0255
    Example: Changed unlinked files are reported separately
      Given a changed file with no matching source_refs
      When source impact is resolved
      Then the file is listed as unlinked

    @bdd-source-changed-json-impacted-record
    @req-REQ-0017
    @ac-AC-0256
    Example: Changed JSON reports modified file and impacted record
      Given a baseline source snapshot and a modified referenced file
      When archledger source changed is run with JSON output
      Then the modified file includes old and new sha256 values
      And the impacted record id and section are reported
