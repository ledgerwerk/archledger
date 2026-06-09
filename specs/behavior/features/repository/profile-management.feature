@area-repository @feature-profile-management
Feature: Profile management

  # Profiles manage documentation and SDD contract layers. BDD remains behavior
  # metadata rather than a profile, and migration from legacy section locations
  # must update config consistently.

  @rule-profile-migration
  Rule: Profile migration moves legacy sections and updates config

    @bdd-profile-migrate-legacy-sections
    Example: Legacy sections are moved into arc42 profile directory
      Given a legacy workspace with sections under the old sections directory
      When archledger profile migrate is run
      Then section files are moved under profiles/arc42/sections
      And the config points at the migrated section directory

  @rule-bdd-not-profile
  Rule: BDD is not a standalone profile

    @bdd-profile-enable-bdd-explains-metadata-layer
    Example: Enabling BDD as a profile explains the model
      Given an initialized workspace
      When archledger profile enable bdd is run
      Then the command explains that BDD is metadata and not a profile
      And no bdd profile is enabled

    @bdd-profile-disable-bdd-explains-metadata-layer
    Example: Disabling BDD as a profile explains the model
      Given an initialized workspace
      When archledger profile disable bdd is run
      Then the command explains that BDD is metadata and not a profile

  @rule-sdd-profile
  Rule: SDD profile changes preserve policy

    @bdd-profile-enable-sdd-preserves-policy
    Example: Enabling SDD preserves existing SDD policy
      Given a workspace with an existing profiles.sdd policy block
      When archledger profile enable sdd is run
      Then the policy block is still present with its existing values
