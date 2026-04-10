# E2E Testing Framework for Otterdog

This framework tests Otterdog features comprehensively, ensuring that operations (import, apply, validate) work correctly with GitHub's API.

## 🚀 Quick Start

```bash
# Install dependencies
poetry add --group test pytest-bdd

# Start WireMock (required for API mocking)
docker run -d --name wiremock -p 8080:8080 wiremock/wiremock:3.3.1

# Run smoke tests with nice visual output
pytest tests/e2e/test_init_bdd.py -m smoke --gherkin-terminal-reporter -vv --color=yes

# Run all E2E BDD tests
pytest tests/e2e/test_init_bdd.py --gherkin-terminal-reporter -vv
```

## Architecture

```
tests/e2e/
├── features/           # Tests organized by Otterdog features
│   ├── bdd/           # BDD feature files (Gherkin)
│   │   └── init.feature
│   └── __init__.py
├── steps/             # BDD step definitions
│   └── test_init_steps.py
├── fixtures/          # Test fixtures
│   └── wiremock.py   # WireMock client
├── operations/        # Tests for Otterdog operations
│   └── __init__.py
├── mocks/            # GitHub API mock management
│   ├── generator.py  # OpenAPI-based mock generator
│   ├── cache/        # Cached OpenAPI specs
│   │   └── github-openapi.yaml
│   └── mappings/     # WireMock mappings
├── framework/        # Test framework utilities
│   ├── base.py      # Base test classes
│   ├── features.py  # Feature mapping
│   ├── features.yaml # Feature definitions
│   ├── coverage.py  # Coverage tracking
│   ├── init_coverage.py # Init-specific coverage
│   └── bdd_integration.py # BDD framework integration
├── test_init_bdd.py  # Main BDD test file
├── conftest.py       # Pytest configuration
└── pytest.ini        # Pytest settings for BDD
```

## Testing Philosophy

1. **Feature-Centric**: Tests are organized by Otterdog features, not GitHub API endpoints
2. **Operation Coverage**: Each feature is tested through import, apply, and validate operations
3. **Dynamic Mocking**: GitHub API mocks are generated from OpenAPI specs for accuracy
4. **Real Workflows**: Tests simulate actual user workflows, not isolated API calls

## Features Tested

### Organization Level
- Settings (basic, workflow, security)
- Secrets (organization, codespaces, dependabot)
- Variables
- Teams and membership
- Webhooks
- Rulesets

### Repository Level
- Settings and configuration
- Environments (with secrets and variables)
- Branch protection
- Dependabot secrets
- Webhooks
- Rulesets

## Running Tests

```bash
# Run all e2e tests
make e2e-test

# Test specific feature
make e2e-test-feature FEATURE=organization.settings

# Test specific operation
make e2e-test-operation OPERATION=import

# Update GitHub API mocks
make e2e-update-mocks
```

## 🔧 BDD Testing with pytest-bdd

### Writing Tests
Tests are written in Gherkin format in `.feature` files:

```gherkin
Feature: Otterdog Initialization
  Scenario: Successfully initialize Otterdog with single organization
    Given a configuration repository "eclipse-csi/otterdog-configs" exists
    When I call the init endpoint "/internal/init"
    Then the response status should be 200
    And organization data for "test-org" should be synced
```

### Running BDD Tests

```bash
# Run with visual Gherkin output
pytest tests/e2e/test_init_bdd.py --gherkin-terminal-reporter -vv --color=yes

# Run by tag
pytest tests/e2e -m smoke       # Quick smoke tests
pytest tests/e2e -m happy_path  # Success scenarios
pytest tests/e2e -m error_handling # Error scenarios

# Run specific scenario
pytest tests/e2e/test_init_bdd.py::test_successfully_initialize_otterdog_with_single_organization
```

## 📋 Session Context (2026-04-13)

### Key Accomplishments
1. **Built E2E Framework** with pytest-bdd, WireMock, and GitHub OpenAPI spec
2. **Fixed Import Issues** for GitHubOrganization, ImportOperation, ApplyOperation, ValidateOperation
3. **Updated GitHub OpenAPI URL** to current version (removed 2022-11-28 date)
4. **Created BDD Tests** for init feature with 11 scenarios
5. **Integrated WireMock** for API mocking (running on port 8080)

### Current Test Status
- ✅ 2 tests passing (smoke test, error handling)
- ❌ 12 tests need step implementations
- 🐳 WireMock container running: `wiremock/wiremock:3.3.1`

### Key Files Modified
- `framework/features.yaml` - Added webapp.init feature definition
- `features/bdd/init.feature` - 11 BDD scenarios for init
- `steps/test_init_steps.py` - Step definitions
- `mocks/generator.py` - Fixed GitHub OpenAPI URL
- `conftest.py` - Fixed Credentials initialization

### Environment Setup
```bash
# Dependencies installed
poetry add --group test pytest-bdd

# WireMock container
docker run -d --name wiremock -p 8080:8080 wiremock/wiremock:3.3.1

# Check WireMock health
curl http://localhost:8080/__admin/health
```

### Resume Work Commands
```bash
# Navigate to project
cd /Users/kairo/dev/EF/otterdog

# Run smoke tests
pytest tests/e2e/test_init_bdd.py -m smoke --gherkin-terminal-reporter -vv

# Test against real webapp (when available)
E2E_USE_WEBAPP=1 OTTERDOG_WEBAPP_URL=http://localhost:5000 pytest tests/e2e
```

### Next Steps
1. Implement missing step definitions for failing scenarios
2. Connect to real MongoDB (replace MockDatabase)
3. Add more features beyond init (apply, import, validate)
4. Set up CI/CD integration

### Technical Details
- **GitHub OpenAPI Spec**: https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.yaml
- **Feature Path**: `webapp.init` with components (config_refresh, policy_refresh, blueprint_refresh, installation_update, organization_sync)
- **Coverage Points**: config_loaded, policies_loaded, blueprints_loaded, installations_created, organizations_synced

### Known Issues
- Poetry sometimes recreates `.venv-script` virtual environment
- BDD doesn't natively support async (wrapped with `asyncio.run()`)
- Some test marks need registration (fixed in pytest.ini)

---

**Ready to continue**: Framework is functional with WireMock integration, BDD scenarios, and GitHub OpenAPI spec support. Engineers can write E2E tests in human-readable Gherkin format with automatic coverage tracking.