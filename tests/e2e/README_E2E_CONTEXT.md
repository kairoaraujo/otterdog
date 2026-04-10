# E2E Testing Framework - Work Context & Summary

## 📅 Session Date: 2026-04-13

## 🎯 What We Accomplished

### 1. **E2E Test Framework Setup**
We built a comprehensive E2E testing framework for Otterdog using pytest-bdd that integrates:
- **BDD (Behavior-Driven Development)** with Gherkin syntax
- **GitHub OpenAPI Specification** for accurate API mocking
- **WireMock** for API stubbing (container running on port 8080)
- **Feature Coverage Tracking** system

### 2. **Key Files Created/Modified**

#### Framework Core:
- `tests/e2e/framework/base.py` - Base test classes (OtterdogE2ETest, OtterdogFeatureTest, OtterdogOperationTest)
- `tests/e2e/framework/features.py` - Feature registry system
- `tests/e2e/framework/features.yaml` - Complete feature mapping including new `webapp.init` feature
- `tests/e2e/framework/coverage.py` - Coverage tracking system
- `tests/e2e/framework/init_coverage.py` - Specific coverage for init feature
- `tests/e2e/framework/bdd_integration.py` - BDD integration layer

#### BDD Tests:
- `tests/e2e/features/bdd/init.feature` - Gherkin scenarios for init operation (11 scenarios)
- `tests/e2e/steps/test_init_steps.py` - Step definitions for init scenarios
- `tests/e2e/test_init_bdd.py` - Main test file that loads BDD scenarios

#### Mocks & Fixtures:
- `tests/e2e/mocks/generator.py` - OpenAPI-based mock generator (URL fixed to current GitHub spec)
- `tests/e2e/fixtures/wiremock.py` - WireMock client and fixtures
- `tests/e2e/mocks/cache/github-openapi.yaml` - Cached GitHub OpenAPI spec

#### Configuration:
- `tests/e2e/conftest.py` - Fixed Credentials initialization (uses `_username` not `username`)
- `tests/e2e/pytest.ini` - BDD test configuration with visual output settings

### 3. **Key Fixes Applied**

1. **Import Errors Fixed:**
   - `GitHubOrganization` → `from otterdog.models.github_organization import GitHubOrganization`
   - `ImportOperation` → `from otterdog.operations.import_configuration import ImportOperation`
   - `ApplyOperation` → `from otterdog.operations.apply import ApplyOperation`
   - `ValidateOperation` → `from otterdog.operations.validate import ValidateOperation`

2. **GitHub OpenAPI URL Updated:**
   - Old: `main/descriptions-2022-11-28/api.github.com/api.github.com.yaml`
   - New: `main/descriptions/api.github.com/api.github.com.yaml`

3. **Async/Await Fixed in BDD:**
   - Wrapped async operations in `asyncio.run()` for synchronous BDD steps

4. **Credentials API Fixed:**
   - Changed from `username="test"` to `_username="test"` pattern

### 4. **Current Test Status**

```bash
# Working tests (2 passing):
✅ test_successfully_initialize_otterdog_with_single_organization (smoke test)
✅ test_handle_missing_configuration_repository_gracefully (error handling)

# Tests needing step implementations (12 failing):
❌ test_initialize_with_multiple_organizations
❌ test_initialization_is_idempotent
❌ test_handle_partial_organization_sync_failure
❌ test_handle_github_api_rate_limiting
❌ test_validate_configuration_before_processing
❌ test_apply_blueprints_during_initialization
❌ test_check_policy_compliance_during_initialization
❌ test_sync_different_resource_types[*]
```

### 5. **Dependencies Installed**
```bash
poetry add --group test pytest-bdd  # BDD support
# Also installed via pip: pytest, pytest-asyncio, aiohttp, pydantic, etc.
```

### 6. **Services Running**
- **WireMock**: Docker container on port 8080
  ```bash
  docker ps | grep wiremock
  # Container ID: af2aa0f49415
  # Image: wiremock/wiremock:3.3.1
  # Port: 0.0.0.0:8080->8080/tcp
  ```

## 🚀 How to Resume Work

### 1. **Check WireMock Status:**
```bash
curl http://localhost:8080/__admin/health
```

### 2. **Run Tests:**
```bash
# Run all E2E BDD tests with nice output
cd /Users/kairo/dev/EF/otterdog
.venv/bin/pytest tests/e2e/test_init_bdd.py --gherkin-terminal-reporter -vv --color=yes

# Run only smoke tests
.venv/bin/pytest tests/e2e/test_init_bdd.py -m smoke --gherkin-terminal-reporter -vv

# Run specific scenario
.venv/bin/pytest tests/e2e/test_init_bdd.py::test_successfully_initialize_otterdog_with_single_organization -v
```

### 3. **Key Environment Variables:**
```bash
# To test against real webapp (when available):
E2E_USE_WEBAPP=1 OTTERDOG_WEBAPP_URL=http://localhost:5000 pytest tests/e2e

# For E2E testing mode:
E2E_TESTING=1 pytest tests/e2e
```

## 📋 Next Steps

1. **Implement Missing Step Definitions**
   - Add step definitions in `test_init_steps.py` for failing scenarios
   - Focus on `datatable` parameter handling for multiple orgs test

2. **Connect to Real Services**
   - MongoDB integration (replace MockDatabase)
   - Real Otterdog webapp when available
   - Real GitHub API with test organization

3. **Extend Coverage**
   - Add more features beyond init (apply, import, validate operations)
   - Create feature files for each Otterdog operation
   - Map all Otterdog models to features

4. **CI/CD Integration**
   - Add GitHub Actions workflow for E2E tests
   - Run smoke tests on every PR
   - Full E2E suite on merge to main

## 🔧 Technical Details

### Feature Definition Structure (webapp.init):
```yaml
webapp:
  init:
    operations: [bootstrap, sync, refresh]
    components:
      - config_refresh
      - policy_refresh
      - blueprint_refresh
      - installation_update
      - organization_sync
    coverage_points:
      - config_loaded
      - policies_loaded
      - blueprints_loaded
      - installations_created
      - organizations_synced
```

### BDD Test Structure:
```gherkin
Feature: Otterdog Initialization
  Scenario: Successfully initialize Otterdog
    Given a configuration repository exists
    When I call the init endpoint
    Then organization data should be synced
```

### Framework Integration:
- Uses GitHub's OpenAPI spec for realistic mocks
- WireMock provides HTTP stubbing
- pytest-bdd enables Gherkin scenarios
- Coverage tracking per feature/scenario

## 💡 Key Insights

1. **pytest-bdd works perfectly** with Otterdog's GitOps model
2. **GitHub's OpenAPI spec** provides all needed mock examples
3. **WireMock integration** enables true E2E testing without hitting real APIs
4. **Feature mapping** in YAML provides clear documentation of Otterdog capabilities
5. **BDD scenarios** serve as both tests and living documentation

## 🐛 Known Issues

1. **Poetry virtual env recreation** - Sometimes recreates .venv-script
2. **Test warnings** - Unknown marks need to be registered in pytest.ini (already fixed)
3. **Async handling** - BDD doesn't natively support async, wrapped with asyncio.run()

## 📚 Resources

- GitHub OpenAPI Spec: https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.yaml
- pytest-bdd docs: https://pytest-bdd.readthedocs.io/
- WireMock docs: https://wiremock.org/docs/
- Otterdog init endpoint: `/internal/init`

---

**Session Summary**: Successfully created a working E2E testing framework using pytest-bdd with GitHub OpenAPI spec integration. The framework is ready for engineers to write comprehensive E2E tests in Gherkin format with automatic coverage tracking.