#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Integration layer between pytest-bdd and Otterdog E2E framework.

Provides utilities to connect BDD scenarios with our testing infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest
from pytest_bdd import given, when, then

from .base import OtterdogE2ETest
from .features import FeatureRegistry
from .coverage import FeatureCoverageTracker


@dataclass
class BDDContext:
    """Context for BDD test execution."""

    test_instance: OtterdogE2ETest
    feature_registry: FeatureRegistry
    coverage_tracker: FeatureCoverageTracker
    scenario_data: Dict[str, Any]
    wiremock_stubs: List[Dict[str, Any]]
    api_calls: List[tuple[str, str]]  # (method, path)
    database_operations: List[tuple[str, str]]  # (collection, operation)

    def __init__(self):
        self.test_instance = None
        self.feature_registry = FeatureRegistry()
        self.coverage_tracker = FeatureCoverageTracker()
        self.scenario_data = {}
        self.wiremock_stubs = []
        self.api_calls = []
        self.database_operations = []


class BDDTestBase(OtterdogE2ETest):
    """Base class for BDD-style E2E tests."""

    def __init__(self, context: BDDContext):
        super().__init__()
        self.context = context

    async def setup_scenario_mocks(self, scenario_name: str):
        """Set up mocks based on scenario requirements."""
        # Use GitHub OpenAPI spec to generate mocks
        from tests.e2e.mocks.generator import OpenAPIMockGenerator

        generator = OpenAPIMockGenerator()
        if not generator.spec:
            await generator.fetch_openapi_spec()

        # Generate mocks for recorded API calls
        for method, path in self.context.api_calls:
            # Find matching OpenAPI operation
            operation = generator.get_operation(method, path)
            if operation:
                # Generate mock based on OpenAPI examples
                mock = generator.generate_mock_from_openapi(operation)
                await self.wiremock.stub_for(mock)

    def track_coverage(self, step_name: str, status: str = "passed"):
        """Track coverage for a BDD step."""
        self.context.coverage_tracker.mark_step_covered(step_name, status)

    def record_api_call(self, method: str, path: str):
        """Record an API call for coverage tracking."""
        self.context.api_calls.append((method, path))
        self.context.coverage_tracker.record_api_call(method, path)

    def record_database_op(self, collection: str, operation: str):
        """Record a database operation for coverage tracking."""
        self.context.database_operations.append((collection, operation))
        self.context.coverage_tracker.record_database_operation(collection, operation)


# Reusable BDD step definitions that work with our framework

@given("the GitHub API returns example data from OpenAPI spec")
def use_openapi_examples(context: BDDContext):
    """Configure mocks to use GitHub OpenAPI examples."""
    context.scenario_data["use_openapi_examples"] = True


@given("WireMock is configured for the scenario")
async def setup_wiremock(context: BDDContext):
    """Set up WireMock with appropriate stubs."""
    if context.test_instance:
        await context.test_instance.setup_scenario_mocks(
            context.scenario_data.get("scenario_name", "default")
        )


@when("I perform a GitHub API call to {method} {path}")
def perform_api_call(context: BDDContext, method: str, path: str):
    """Record a GitHub API call."""
    context.test_instance.record_api_call(method, path)


@when("I perform database operation {operation} on {collection}")
def perform_db_operation(context: BDDContext, operation: str, collection: str):
    """Record a database operation."""
    context.test_instance.record_database_op(collection, operation)


@then("the coverage report should show {coverage_percent}% coverage")
def check_coverage(context: BDDContext, coverage_percent: str):
    """Verify coverage percentage."""
    coverage = context.coverage_tracker.get_coverage_percentage()
    expected = float(coverage_percent)
    assert coverage >= expected, f"Coverage {coverage}% is below expected {expected}%"


@then("all API calls should match OpenAPI specification")
def verify_api_compliance(context: BDDContext):
    """Verify all API calls comply with OpenAPI spec."""
    from tests.e2e.mocks.generator import OpenAPIMockGenerator

    generator = OpenAPIMockGenerator()

    for method, path in context.api_calls:
        operation = generator.get_operation(method, path)
        assert operation is not None, f"API call {method} {path} not found in OpenAPI spec"


# Pytest fixtures for BDD tests

@pytest.fixture
def bdd_context():
    """Create a BDD context for the test."""
    return BDDContext()


@pytest.fixture
async def bdd_test(bdd_context, wiremock_client, github_provider):
    """Create a BDD test instance with all dependencies."""
    test = BDDTestBase(bdd_context)
    test.wiremock = wiremock_client
    test.github = github_provider
    bdd_context.test_instance = test
    return test


# Hook to generate coverage report after test run

def pytest_sessionfinish(session, exitstatus):
    """Generate coverage report at end of test session."""
    # This would be called after all BDD tests complete
    # Could generate HTML report, JSON output, etc.
    pass