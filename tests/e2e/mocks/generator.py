#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
GitHub API mock generator using OpenAPI specifications.

Generates WireMock stubs from GitHub's official OpenAPI specs.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import yaml

from otterdog.utils import get_logger
from tests.e2e.framework.features import FeatureRegistry, GitHubAPIEndpoint

_logger = get_logger(__name__)


class OpenAPIMockGenerator:
    """Generate WireMock mocks from GitHub's OpenAPI specification."""

    GITHUB_OPENAPI_URL = (
        "https://raw.githubusercontent.com/github/rest-api-description/"
        "main/descriptions/api.github.com/api.github.com.yaml"
    )

    def __init__(self, cache_dir: Path = None):
        """Initialize the mock generator."""
        self.cache_dir = cache_dir or Path(__file__).parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.spec: Optional[Dict[str, Any]] = None
        self.feature_registry = FeatureRegistry()

    async def fetch_openapi_spec(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch GitHub's OpenAPI specification."""
        cache_file = self.cache_dir / "github-openapi.yaml"

        # Check cache (valid for 7 days)
        if not force_refresh and cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=7):
                _logger.info("Using cached OpenAPI spec")
                with open(cache_file) as f:
                    self.spec = yaml.safe_load(f)
                return self.spec

        # Fetch fresh spec
        _logger.info("Fetching GitHub OpenAPI spec...")
        async with aiohttp.ClientSession() as session:
            async with session.get(self.GITHUB_OPENAPI_URL) as response:
                response.raise_for_status()
                content = await response.text()

                # Save to cache
                cache_file.write_text(content)
                self.spec = yaml.safe_load(content)

        _logger.info(f"OpenAPI spec fetched and cached at {cache_file}")
        return self.spec

    def get_operation(self, method: str, path: str) -> Optional[Dict[str, Any]]:
        """Get operation details from OpenAPI spec."""
        if not self.spec:
            raise ValueError("OpenAPI spec not loaded. Call fetch_openapi_spec first.")

        # Find path in spec
        paths = self.spec.get("paths", {})

        # Try exact match first
        if path in paths:
            path_item = paths[path]
            return path_item.get(method.lower())

        # Try pattern matching for parameterized paths
        for spec_path, path_item in paths.items():
            if self._path_matches(path, spec_path):
                return path_item.get(method.lower())

        return None

    def _path_matches(self, actual: str, pattern: str) -> bool:
        """Check if actual path matches OpenAPI pattern."""
        # Convert OpenAPI path to regex
        regex_pattern = pattern
        regex_pattern = regex_pattern.replace("{", "(?P<")
        regex_pattern = regex_pattern.replace("}", ">[^/]+)")
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, actual))

    def generate_mock_for_endpoint(
        self,
        endpoint: GitHubAPIEndpoint,
        scenario_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate WireMock stub for a GitHub API endpoint."""
        operation = self.get_operation(endpoint.method, endpoint.path)

        if not operation:
            _logger.warning(f"No OpenAPI spec found for {endpoint.method} {endpoint.path}")
            return self._generate_basic_mock(endpoint)

        # Extract response from OpenAPI
        response = self._extract_response(operation, scenario_data)

        # Build WireMock stub
        stub = {
            "name": operation.get("summary", f"{endpoint.method} {endpoint.path}"),
            "request": {
                "method": endpoint.method,
                "urlPathPattern": self._convert_to_wiremock_pattern(endpoint.path),
            },
            "response": {
                "status": response.get("status", 200),
                "headers": {
                    "Content-Type": "application/json",
                    "X-RateLimit-Remaining": "5000",
                    "X-RateLimit-Limit": "5000",
                },
                "jsonBody": response.get("body", {}),
            },
        }

        # Add request body schema if applicable
        if endpoint.method in ["POST", "PUT", "PATCH"]:
            request_body = operation.get("requestBody", {})
            if "content" in request_body:
                content = request_body["content"].get("application/json", {})
                if "schema" in content:
                    stub["request"]["bodyPatterns"] = [
                        {"matchesJsonSchema": json.dumps(content["schema"])}
                    ]

        return stub

    def _extract_response(
        self,
        operation: Dict[str, Any],
        scenario_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Extract response from OpenAPI operation."""
        responses = operation.get("responses", {})

        # Try success responses
        for status in ["200", "201", "204"]:
            if status in responses:
                response_def = responses[status]

                # Handle no content responses
                if status == "204":
                    return {"status": 204, "body": None}

                # Extract JSON response
                if "content" in response_def:
                    content = response_def["content"].get("application/json", {})

                    # Use example if available
                    if "example" in content:
                        return {"status": int(status), "body": content["example"]}

                    # Use examples if available
                    if "examples" in content:
                        first_example = list(content["examples"].values())[0]
                        if "value" in first_example:
                            return {"status": int(status), "body": first_example["value"]}

                    # Generate from schema
                    if "schema" in content:
                        body = self._generate_from_schema(content["schema"], scenario_data)
                        return {"status": int(status), "body": body}

        # Default response
        return {"status": 200, "body": {}}

    def _generate_from_schema(
        self,
        schema: Dict[str, Any],
        scenario_data: Dict[str, Any] = None,
    ) -> Any:
        """Generate example data from JSON Schema."""
        if scenario_data is None:
            scenario_data = {}

        # Handle references
        if "$ref" in schema:
            ref_path = schema["$ref"].split("/")[-1]
            if self.spec and "components" in self.spec:
                schema = self.spec["components"]["schemas"].get(ref_path, schema)

        # Generate based on type
        schema_type = schema.get("type")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for prop_name, prop_schema in properties.items():
                # Use scenario data if available
                if prop_name in scenario_data:
                    result[prop_name] = scenario_data[prop_name]
                elif prop_name in required or "example" in prop_schema:
                    result[prop_name] = self._generate_from_schema(prop_schema, scenario_data)

            return result

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            # Generate 1-3 items based on context
            count = scenario_data.get("_array_count", 2)
            return [
                self._generate_from_schema(items_schema, scenario_data)
                for _ in range(count)
            ]

        elif schema_type == "string":
            if "enum" in schema:
                return schema["enum"][0]
            return schema.get("example", scenario_data.get("_string_value", "example-string"))

        elif schema_type == "integer":
            return schema.get("example", scenario_data.get("_integer_value", 123))

        elif schema_type == "number":
            return schema.get("example", scenario_data.get("_number_value", 123.45))

        elif schema_type == "boolean":
            return schema.get("example", scenario_data.get("_boolean_value", True))

        else:
            # Handle anyOf, oneOf, etc.
            if "anyOf" in schema:
                return self._generate_from_schema(schema["anyOf"][0], scenario_data)
            elif "oneOf" in schema:
                return self._generate_from_schema(schema["oneOf"][0], scenario_data)

        return None

    def _convert_to_wiremock_pattern(self, path: str) -> str:
        """Convert OpenAPI path to WireMock URL pattern."""
        # Convert {param} to regex pattern
        pattern = path
        pattern = re.sub(r"\{([^}]+)\}", r"[^/]+", pattern)
        return pattern

    def _generate_basic_mock(self, endpoint: GitHubAPIEndpoint) -> Dict[str, Any]:
        """Generate a basic mock when OpenAPI spec is not available."""
        return {
            "name": f"{endpoint.method} {endpoint.path}",
            "request": {
                "method": endpoint.method,
                "urlPathPattern": self._convert_to_wiremock_pattern(endpoint.path),
            },
            "response": {
                "status": 200 if endpoint.method == "GET" else 201,
                "headers": {
                    "Content-Type": "application/json",
                },
                "jsonBody": {},
            },
        }

    async def generate_mocks_for_feature(
        self,
        feature_path: str,
        operation: str = "import",
    ) -> List[Dict[str, Any]]:
        """Generate all mocks needed for an Otterdog feature."""
        feature = self.feature_registry.get_feature(feature_path)
        if not feature:
            raise ValueError(f"Feature not found: {feature_path}")

        # Get all APIs for this feature
        endpoints = feature.get_all_apis(operation)

        # Generate mocks for each endpoint
        mocks = []
        for endpoint in endpoints:
            mock = self.generate_mock_for_endpoint(endpoint)
            mocks.append(mock)

        return mocks

    async def generate_mocks_for_operation(
        self,
        operation: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mocks for all features in an operation."""
        features = self.feature_registry.get_features_for_operation(operation)

        mocks_by_feature = {}
        for feature in features:
            feature_mocks = await self.generate_mocks_for_feature(
                feature.full_path,
                operation,
            )
            mocks_by_feature[feature.full_path] = feature_mocks

        return mocks_by_feature

    def save_mocks(
        self,
        mocks: List[Dict[str, Any]],
        output_file: Path,
    ) -> None:
        """Save mocks to a WireMock mappings file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        mappings = {"mappings": mocks}
        with open(output_file, "w") as f:
            json.dump(mappings, f, indent=2)

        _logger.info(f"Saved {len(mocks)} mocks to {output_file}")


async def update_all_mocks():
    """Update all mock files from OpenAPI spec."""
    generator = OpenAPIMockGenerator()
    await generator.fetch_openapi_spec(force_refresh=True)

    output_dir = Path(__file__).parent / "mappings"

    # Generate mocks for each operation
    for operation in ["import", "apply", "validate"]:
        _logger.info(f"Generating mocks for {operation} operation...")
        mocks_by_feature = await generator.generate_mocks_for_operation(operation)

        for feature_path, mocks in mocks_by_feature.items():
            output_file = output_dir / operation / f"{feature_path.replace('.', '_')}.json"
            generator.save_mocks(mocks, output_file)

    _logger.info("All mocks updated successfully")


if __name__ == "__main__":
    import asyncio
    asyncio.run(update_all_mocks())