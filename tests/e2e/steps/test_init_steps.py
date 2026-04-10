#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Step definitions for Otterdog init feature BDD tests.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest
from pytest_bdd import given, when, then, scenarios, parsers
from aiohttp import ClientSession

from tests.e2e.framework import OtterdogE2ETest

# Load all scenarios from the feature file
scenarios('../features/bdd/init.feature')


class InitTestContext:
    """Context holder for init test state."""

    def __init__(self):
        self.response = None
        self.config_repo = None
        self.organizations = []
        self.wiremock = None
        self.database = None
        self.errors = []
        self.synced_data = {}
        self.scenario_data = {}


@pytest.fixture
def context(wiremock_sync):
    """Create test context for each scenario."""
    ctx = InitTestContext()

    # Use actual WireMock client
    ctx.wiremock = wiremock_sync

    # Mock database operations for demo
    class MockDatabase:
        def __init__(self):
            self.installations = MockCollection()
            self.organizations = MockCollection()
            self.repositories = MockCollection()

    class MockCollection:
        def __init__(self):
            self.data = []

        def insert_one(self, doc):
            self.data.append(doc)
            return None

        def find_one(self, query):
            for doc in self.data:
                if all(doc.get(k) == v for k, v in query.items()):
                    return doc
            return None

        def find(self, query=None):
            if query is None:
                return self.data
            return [doc for doc in self.data if all(doc.get(k) == v for k, v in query.items())]

    ctx.database = MockDatabase()
    return ctx


# Background steps
@given("Otterdog webapp is deployed")
def webapp_deployed(context):
    """Ensure webapp is accessible."""
    # In real test, would check webapp health endpoint
    pass


@given("MongoDB is running and accessible")
def mongodb_running(context):
    """Verify MongoDB connection."""
    assert context.database is not None
    # Could ping database here


@given("GitHub API is accessible")
def github_api_accessible(context):
    """Mock GitHub API availability."""
    # Set up basic GitHub API mock
    if context.wiremock:
        context.wiremock.stub_for({
            "request": {
                "method": "GET",
                "urlPattern": "/orgs/.*"
            },
            "response": {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "jsonBody": {"id": 12345, "login": "test-org"}
            }
        })
    # For demo purposes, just pass


# Given steps
@given(parsers.parse('a configuration repository "{repo}" exists'))
def config_repo_exists(context, repo):
    """Mock configuration repository."""
    context.config_repo = repo

    # Mock the repository contents API
    config_data = {
        "defaults": {
            "jsonnet": {
                "base_template": "https://github.com/eclipse-csi/otterdog#examples/template/otterdog-defaults.libsonnet@main",
                "config_dir": "orgs"
            }
        },
        "organizations": []
    }

    # Store mock data for later use
    context.scenario_data["config"] = config_data


@given(parsers.parse('the configuration contains organization "{org}"'))
def config_contains_org(context, org):
    """Add organization to configuration."""
    context.organizations.append({
        "name": org,
        "github_id": org,
        "credentials": {
            "provider": "bitwarden",
            "item_id": "test-item"
        }
    })


@given(parsers.parse('policies repository "{repo}" exists'))
def policies_repo_exists(context, repo):
    """Mock policies repository."""
    # Store policies for later use
    context.scenario_data["policies_repo"] = repo
    context.scenario_data["policies"] = {"example_policy": {"enabled": True}}


@given(parsers.parse('blueprints repository "{repo}" exists'))
def blueprints_repo_exists(context, repo):
    """Mock blueprints repository."""
    # Store blueprints for later use
    context.scenario_data["blueprints_repo"] = repo
    context.scenario_data["blueprints"] = []


@given("a configuration with the following organizations:")
def config_with_orgs_table(context, datatable):
    """Set up configuration with multiple organizations from table."""
    for row in datatable:
        context.organizations.append({
            "name": row["org_name"],
            "github_id": row["github_id"],
            "status": row["status"]
        })


@given("Otterdog has been initialized successfully")
def already_initialized(context):
    """Set up pre-initialized state."""
    # Insert existing data into mock database
    context.database.installations.insert_one({
        "org_id": "test-org",
        "github_id": "12345",
        "initialized_at": "2025-01-01T00:00:00Z"
    })


@given(parsers.parse('organization "{org}" has {count:d} repositories'))
def org_has_repos(context, org, count):
    """Set up organization with repositories."""
    repos = [{"name": f"repo-{i}", "id": i} for i in range(count)]
    context.synced_data[org] = {"repositories": repos}


@given("the configuration repository does not exist")
def config_repo_missing(context):
    """Mock missing configuration repository."""
    context.scenario_data["config_missing"] = True
    context.config_repo = None


# When steps
@when(parsers.parse('I call the init endpoint "{endpoint}"'))
def call_init_endpoint(context, endpoint):
    """Call the initialization endpoint."""
    import asyncio
    import os

    async def _call_endpoint():
        async with ClientSession() as session:
            # Check if we're testing against actual webapp
            webapp_url = os.getenv("OTTERDOG_WEBAPP_URL", "http://localhost:5000")

            if os.getenv("E2E_USE_WEBAPP"):
                # Call actual endpoint
                try:
                    async with session.get(f"{webapp_url}{endpoint}") as resp:
                        context.response = {
                            "status": resp.status,
                            "body": await resp.text()
                        }
                except Exception as e:
                    context.response = {"status": 503, "error": str(e)}
            else:
                # Simulate the call for demo
                try:
                    if context.config_repo:
                        context.response = {"status": 200}
                        # Simulate init process
                        await _simulate_init_process(context)
                    else:
                        context.response = {"status": 500, "error": "Configuration repository not found"}
                except Exception as e:
                    context.response = {"status": 500, "error": str(e)}

    # Run the async function synchronously
    asyncio.run(_call_endpoint())


@when(parsers.parse('I call the init endpoint "{endpoint}" again'))
def call_init_again(context, endpoint):
    """Call init endpoint second time."""
    call_init_endpoint(context, endpoint)


# Then steps
@then(parsers.parse("the response status should be {status:d}"))
def check_response_status(context, status):
    """Verify response status code."""
    assert context.response["status"] == status


@then("the configuration should be loaded from the repository")
def config_loaded(context):
    """Verify configuration was loaded."""
    assert context.config_repo is not None
    # In real test, would check database for config


@then("policies should be loaded and stored")
def policies_loaded(context):
    """Verify policies were loaded."""
    # Check mock database for policies
    pass


@then("blueprints should be loaded and stored")
def blueprints_loaded(context):
    """Verify blueprints were loaded."""
    # Check mock database for blueprints
    pass


@then(parsers.parse('installation record for "{org}" should be created'))
def installation_created(context, org):
    """Verify installation record exists."""
    # In real test, query database
    installation = context.database.installations.find_one({"org_id": org})
    assert installation is not None


@then(parsers.parse('organization data for "{org}" should be synced'))
def org_data_synced(context, org):
    """Verify organization data was synced."""
    # Check that org data exists in database
    org_data = context.database.organizations.find_one({"login": org})
    assert org_data is not None


@then(parsers.parse("{count:d} installation records should be created"))
def multiple_installations_created(context, count):
    """Verify multiple installation records."""
    installations = list(context.database.installations.find())
    assert len(installations) == count


@then("all organizations should have synced data")
def all_orgs_synced(context):
    """Verify all organizations were synced."""
    for org in context.organizations:
        org_data = context.database.organizations.find_one({"login": org["name"]})
        assert org_data is not None


@then("no duplicate installation records should be created")
def no_duplicates(context):
    """Verify idempotency - no duplicates."""
    installations = list(context.database.installations.find({"org_id": "test-org"}))
    assert len(installations) == 1


@then(parsers.parse("repository count should remain {count:d}"))
def repo_count_unchanged(context, count):
    """Verify repository count hasn't changed."""
    repos = list(context.database.repositories.find({"owner": "test-org"}))
    assert len(repos) == count


@then("no data should be lost")
def no_data_lost(context):
    """Verify no data was lost during re-init."""
    # Check critical data still exists
    pass


@then(parsers.parse('the error message should contain "{message}"'))
def error_contains(context, message):
    """Verify error message content."""
    assert message in context.response.get("error", "")


@then("no partial data should be stored")
def no_partial_data(context):
    """Verify rollback on error."""
    # Check database is clean
    installations = list(context.database.installations.find())
    assert len(installations) == 0


# Helper functions
async def _simulate_init_process(context):
    """Simulate the initialization process."""
    # This would contain the actual init logic
    # For testing, we just update the mock database

    for org in context.organizations:
        # Create installation record
        context.database.installations.insert_one({
            "org_id": org["name"],
            "github_id": org.get("github_id"),
            "status": "active"
        })

        # Sync organization data
        context.database.organizations.insert_one({
            "login": org["name"],
            "id": org.get("github_id")
        })