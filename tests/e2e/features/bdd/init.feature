Feature: Otterdog Initialization
  As a DevOps engineer
  I want to initialize Otterdog webapp
  So that it can manage GitHub organizations as code

  Background:
    Given Otterdog webapp is deployed
    And MongoDB is running and accessible
    And GitHub API is accessible

  @happy_path @smoke
  Scenario: Successfully initialize Otterdog with single organization
    Given a configuration repository "eclipse-csi/otterdog-configs" exists
    And the configuration contains organization "test-org"
    And policies repository "eclipse-csi/otterdog-policies" exists
    And blueprints repository "eclipse-csi/otterdog-blueprints" exists
    When I call the init endpoint "/internal/init"
    Then the response status should be 200
    And the configuration should be loaded from the repository
    And policies should be loaded and stored
    And blueprints should be loaded and stored
    And installation record for "test-org" should be created
    And organization data for "test-org" should be synced

  @multiple_orgs
  Scenario: Initialize with multiple organizations
    Given a configuration with the following organizations:
      | org_name      | github_id | status  |
      | eclipse-ee4j  | 12345678  | active  |
      | eclipse-jdt   | 23456789  | active  |
      | eclipse-cbi   | 34567890  | active  |
    When I call the init endpoint "/internal/init"
    Then the response status should be 200
    And 3 installation records should be created
    And all organizations should have synced data

  @idempotency
  Scenario: Initialization is idempotent
    Given Otterdog has been initialized successfully
    And organization "test-org" has 10 repositories
    When I call the init endpoint "/internal/init" again
    Then the response status should be 200
    And no duplicate installation records should be created
    And repository count should remain 10
    And no data should be lost

  @error_handling
  Scenario: Handle missing configuration repository gracefully
    Given the configuration repository does not exist
    When I call the init endpoint "/internal/init"
    Then the response status should be 500
    And the error message should contain "Configuration repository not found"
    And no partial data should be stored

  @partial_sync
  Scenario: Handle partial organization sync failure
    Given a configuration with organizations "org-a" and "org-b"
    And "org-a" is accessible via GitHub API
    But "org-b" returns 404 from GitHub API
    When I call the init endpoint "/internal/init"
    Then the response status should be 200
    And installation record for "org-a" should be created
    And organization data for "org-a" should be synced
    And "org-b" should be marked as failed in the database
    And error details for "org-b" should be logged

  @github_api_rate_limit
  Scenario: Handle GitHub API rate limiting
    Given GitHub API rate limit is nearly exhausted
    When I call the init endpoint "/internal/init"
    Then the init process should pause when rate limit is hit
    And should resume after rate limit reset
    And all data should be eventually synced

  @config_validation
  Scenario: Validate configuration before processing
    Given a configuration with invalid JSON structure
    When I call the init endpoint "/internal/init"
    Then the response status should be 400
    And the error should indicate the validation failure
    And no database changes should occur

  @blueprint_application
  Scenario: Apply blueprints during initialization
    Given blueprints define required files for repositories
    And organization "test-org" has repositories without required files
    When I call the init endpoint "/internal/init"
    Then blueprints should be loaded
    And non-compliant repositories should be identified
    And blueprint violations should be recorded

  @policy_enforcement
  Scenario: Check policy compliance during initialization
    Given policies define security requirements
    And organization "test-org" has non-compliant settings
    When I call the init endpoint "/internal/init"
    Then policies should be evaluated
    And policy violations should be recorded
    And compliance status should be stored

  @incremental_sync
  Scenario Outline: Sync different resource types
    Given organization "test-org" has <resource_type>
    When I call the init endpoint "/internal/init"
    Then <resource_type> should be fetched from GitHub
    And <resource_type> should be stored in the database
    And sync timestamp for <resource_type> should be updated

    Examples:
      | resource_type            |
      | repositories             |
      | teams                    |
      | secrets                  |
      | organization_settings    |
      | webhooks                 |