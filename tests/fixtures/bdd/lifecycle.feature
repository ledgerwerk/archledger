@lifecycle @approval
Feature: Task lifecycle gates

  Rule: Implementation requires an accepted plan

    @happy-path
    Scenario: Agent tries to implement before approval
      Given a task has a proposed plan
      And the plan has not been approved by the user
      When the agent starts implementation
      Then implementation is blocked
      And the task remains in planning or review state

    Scenario: Agent implements after approval
      Given a task has an approved plan
      When the agent starts implementation
      Then implementation proceeds normally
