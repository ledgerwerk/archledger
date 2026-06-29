@area-repository @feature-repository-schemas
Feature: JSON schema installation

  JSON schemas can be installed to external locations for tooling
  integration.

  @rule-install
  Rule: Schema install writes schema files to target directory

    @bdd-schema-install-jsonschema
    @req-REQ-0014
    @ac-AC-0207
    Example: Install returns the target path for jsonschema
      Given a workspace
      When schema install jsonschema is run
      Then the target path is returned

    @bdd-schema-install-legacy-refuses-overwrite
    @req-REQ-0014
    @ac-AC-0208
    Example: Install refuses to overwrite without force flag
      Given a target directory with existing schema
      When schema install is run without --force
      Then an error about existing file is returned

    @bdd-schema-install-force-overwrite
    @req-REQ-0014
    @ac-AC-0209
    Example: Install overwrites with force flag
      Given a target directory with existing schema
      When schema install --force is run
      Then the schema file is overwritten
