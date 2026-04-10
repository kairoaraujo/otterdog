#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Base classes for E2E tests.

Provides common functionality for testing Otterdog features and operations.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

from otterdog.jsonnet import JsonnetConfig
from otterdog.models.github_organization import GitHubOrganization
from otterdog.utils import get_logger

from .features import FeatureRegistry

_logger = get_logger(__name__)


class OtterdogE2ETest:
    """Base class for all Otterdog E2E tests."""

    @pytest.fixture(autouse=True)
    def setup_base(self, tmp_path, github_provider, wiremock):
        """Set up base test environment."""
        self.temp_dir = tmp_path
        self.github_provider = github_provider
        self.wiremock = wiremock
        self.feature_registry = FeatureRegistry()

    def create_config(self, config_data: Dict[str, Any]) -> JsonnetConfig:
        """Create a Jsonnet configuration from dictionary data."""
        config_file = self.temp_dir / "test-config.jsonnet"

        # Convert to Jsonnet format
        jsonnet_content = f"""
local org = {json.dumps(config_data, indent=2)};
org
"""
        config_file.write_text(jsonnet_content)
        return JsonnetConfig(str(config_file))

    def create_yaml_config(self, yaml_content: str) -> JsonnetConfig:
        """Create a configuration from YAML string."""
        data = yaml.safe_load(yaml_content)
        return self.create_config(data)

    async def setup_mock_response(
        self,
        method: str,
        path: str,
        response_body: Dict[str, Any] = None,
        status: int = 200,
    ):
        """Set up a single mock response."""
        await self.wiremock.stub_for({
            "request": {
                "method": method,
                "urlPathPattern": path.replace("{", "[^/]+").replace("}", ""),
            },
            "response": {
                "status": status,
                "headers": {
                    "Content-Type": "application/json",
                    "X-RateLimit-Remaining": "5000",
                },
                "jsonBody": response_body or {},
            },
        })

    async def verify_api_called(
        self,
        method: str,
        path_pattern: str,
        times: int = 1,
    ) -> None:
        """Verify that an API endpoint was called."""
        calls = await self.wiremock.get_requests()

        matching_calls = [
            call for call in calls
            if call["request"]["method"] == method
            and path_pattern in call["request"]["url"]
        ]

        assert len(matching_calls) == times, (
            f"Expected {method} {path_pattern} to be called {times} times, "
            f"but was called {len(matching_calls)} times"
        )


class OtterdogFeatureTest(OtterdogE2ETest):
    """Base class for testing specific Otterdog features."""

    feature_path: str = None  # Override in subclasses

    @pytest.fixture(autouse=True)
    def setup_feature(self):
        """Set up feature-specific test environment."""
        if self.feature_path:
            self.feature = self.feature_registry.get_feature(self.feature_path)
            assert self.feature, f"Feature not found: {self.feature_path}"

    async def setup_feature_mocks(
        self,
        operation: str,
        scenario_data: Dict[str, Any] = None,
    ):
        """Set up all mocks needed for this feature."""
        if not self.feature:
            return

        endpoints = self.feature.get_all_apis(operation)

        from tests.e2e.mocks.generator import OpenAPIMockGenerator
        generator = OpenAPIMockGenerator()

        # Load OpenAPI spec if not loaded
        if not generator.spec:
            await generator.fetch_openapi_spec()

        for endpoint in endpoints:
            mock = generator.generate_mock_for_endpoint(endpoint, scenario_data)
            await self.wiremock.stub_for(mock)

    def assert_feature_imported(
        self,
        organization: GitHubOrganization,
        expected_values: Dict[str, Any] = None,
    ):
        """Assert that the feature was correctly imported."""
        # This should be overridden in subclasses
        pass

    def assert_feature_applied(
        self,
        result: Dict[str, Any],
        expected_changes: List[str] = None,
    ):
        """Assert that the feature was correctly applied."""
        # This should be overridden in subclasses
        pass


class OtterdogOperationTest(OtterdogE2ETest):
    """Base class for testing Otterdog operations."""

    operation: str = None  # Override in subclasses

    async def setup_operation_mocks(self, feature_paths: List[str] = None):
        """Set up mocks for all features in an operation."""
        if feature_paths:
            features_to_mock = [
                self.feature_registry.get_feature(path)
                for path in feature_paths
            ]
        else:
            # Get all features for this operation
            features_to_mock = self.feature_registry.get_features_for_operation(
                self.operation
            )

        from tests.e2e.mocks.generator import OpenAPIMockGenerator
        generator = OpenAPIMockGenerator()

        if not generator.spec:
            await generator.fetch_openapi_spec()

        for feature in features_to_mock:
            if feature:
                endpoints = feature.get_all_apis(self.operation)
                for endpoint in endpoints:
                    mock = generator.generate_mock_for_endpoint(endpoint)
                    await self.wiremock.stub_for(mock)

    def create_test_organization(
        self,
        org_name: str = "test-org",
        with_features: List[str] = None,
    ) -> Dict[str, Any]:
        """Create a test organization configuration."""
        org = {
            "name": org_name,
            "settings": {
                "billing_email": f"admin@{org_name}.example.com",
                "default_repository_permission": "read",
            },
        }

        # Add requested features
        if with_features:
            for feature_path in with_features:
                self._add_feature_to_org(org, feature_path)

        return org

    def _add_feature_to_org(self, org: Dict[str, Any], feature_path: str):
        """Add a feature to the organization configuration."""
        # This is a simplified implementation
        # In reality, this would create proper test data for each feature
        parts = feature_path.split(".")

        if parts[0] == "organization":
            if parts[1] == "secrets" and len(parts) > 2:
                if "secrets" not in org:
                    org["secrets"] = []
                org["secrets"].append({
                    "name": "TEST_SECRET",
                    "value": "test-value",
                })
            elif parts[1] == "teams":
                if "teams" not in org:
                    org["teams"] = []
                org["teams"].append({
                    "name": "test-team",
                    "description": "Test team",
                })

        elif parts[0] == "repository":
            if "repositories" not in org:
                org["repositories"] = []

            if not org["repositories"]:
                org["repositories"].append({
                    "name": "test-repo",
                })

            repo = org["repositories"][0]

            if parts[1] == "environments" and len(parts) > 2:
                if "environments" not in repo:
                    repo["environments"] = []

                if not repo["environments"]:
                    repo["environments"].append({
                        "name": "production",
                    })

                env = repo["environments"][0]

                if parts[2] == "env_secret":
                    if "secrets" not in env:
                        env["secrets"] = []
                    env["secrets"].append({
                        "name": "ENV_SECRET",
                        "value": "secret-value",
                    })
                elif parts[2] == "env_variable":
                    if "variables" not in env:
                        env["variables"] = []
                    env["variables"].append({
                        "name": "ENV_VAR",
                        "value": "var-value",
                    })