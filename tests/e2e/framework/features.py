#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Otterdog feature registry and mapping.

Maps Otterdog features to models, operations, and GitHub APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from otterdog.utils import get_logger

_logger = get_logger(__name__)


@dataclass
class GitHubAPIEndpoint:
    """Represents a GitHub API endpoint."""

    method: str
    path: str
    description: Optional[str] = None

    def matches(self, method: str, url: str) -> bool:
        """Check if this endpoint matches the given method and URL."""
        if self.method != method:
            return False

        # Convert path pattern to regex
        import re
        pattern = self.path
        pattern = pattern.replace("{", "(?P<")
        pattern = pattern.replace("}", ">[^/]+)")
        pattern = f"^{pattern}$"

        return bool(re.match(pattern, url))


@dataclass
class OtterdogFeature:
    """Represents an Otterdog feature."""

    id: str
    description: str
    model: Optional[str] = None
    fields: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    github_apis: Dict[str, List[GitHubAPIEndpoint]] = field(default_factory=dict)
    children: Dict[str, OtterdogFeature] = field(default_factory=dict)
    parent: Optional[OtterdogFeature] = None
    pr_reference: Optional[str] = None
    embedded: bool = False

    @property
    def full_path(self) -> str:
        """Get the full path of this feature."""
        parts = []
        current = self
        while current:
            parts.append(current.id)
            current = current.parent
        return ".".join(reversed(parts))

    def get_all_apis(self, operation: str = None) -> List[GitHubAPIEndpoint]:
        """Get all GitHub APIs for this feature and its children."""
        apis = []

        # Add own APIs
        if operation:
            apis.extend(self.github_apis.get(operation, []))
        else:
            for op_apis in self.github_apis.values():
                apis.extend(op_apis)

        # Add children's APIs
        for child in self.children.values():
            apis.extend(child.get_all_apis(operation))

        return apis

    def is_from_pr(self, pr_number: str) -> bool:
        """Check if this feature is from a specific PR."""
        return self.pr_reference == pr_number


class FeatureRegistry:
    """Registry of all Otterdog features."""

    def __init__(self, features_file: Path = None):
        """Initialize the feature registry."""
        if features_file is None:
            features_file = Path(__file__).parent / "features.yaml"

        self.features: Dict[str, OtterdogFeature] = {}
        self.features_by_model: Dict[str, OtterdogFeature] = {}
        self.features_by_path: Dict[str, OtterdogFeature] = {}

        if features_file.exists():
            self._load_features(features_file)
        else:
            _logger.warning(f"Features file not found: {features_file}")

    def _load_features(self, features_file: Path) -> None:
        """Load features from YAML file."""
        with open(features_file) as f:
            data = yaml.safe_load(f)

        for category_id, category_data in data.get("features", {}).items():
            self._process_feature(category_id, category_data, parent=None)

    def _process_feature(
        self,
        feature_id: str,
        feature_data: Dict[str, Any],
        parent: Optional[OtterdogFeature] = None,
    ) -> OtterdogFeature:
        """Process a feature from the YAML data."""
        # Create feature object
        feature = OtterdogFeature(
            id=feature_id,
            description=feature_data.get("description", ""),
            model=feature_data.get("model"),
            fields=feature_data.get("fields", []),
            operations=feature_data.get("operations", []),
            parent=parent,
            pr_reference=feature_data.get("pr_reference"),
            embedded=feature_data.get("embedded", False),
        )

        # Process GitHub APIs
        github_apis = feature_data.get("github_apis", {})
        for operation, endpoints in github_apis.items():
            feature.github_apis[operation] = [
                GitHubAPIEndpoint(
                    method=ep.get("method"),
                    path=ep.get("path"),
                    description=ep.get("description"),
                )
                for ep in endpoints
            ]

        # Process children
        children_data = feature_data.get("children", {})
        for child_id, child_data in children_data.items():
            child = self._process_feature(child_id, child_data, parent=feature)
            feature.children[child_id] = child

        # Register feature
        self.features[feature_id] = feature
        self.features_by_path[feature.full_path] = feature

        if feature.model:
            self.features_by_model[feature.model] = feature

        return feature

    def get_feature(self, path: str) -> Optional[OtterdogFeature]:
        """Get a feature by its path."""
        return self.features_by_path.get(path)

    def get_feature_by_model(self, model_class: str) -> Optional[OtterdogFeature]:
        """Get a feature by its model class."""
        return self.features_by_model.get(model_class)

    def get_features_for_operation(self, operation: str) -> List[OtterdogFeature]:
        """Get all features that support a specific operation."""
        features = []

        def collect_features(feature: OtterdogFeature):
            if operation in feature.operations or operation in feature.github_apis:
                features.append(feature)
            for child in feature.children.values():
                collect_features(child)

        for root_feature in self.features.values():
            collect_features(root_feature)

        return features

    def get_features_from_pr(self, pr_number: str) -> List[OtterdogFeature]:
        """Get all features from a specific PR."""
        features = []

        def collect_pr_features(feature: OtterdogFeature):
            if feature.is_from_pr(pr_number):
                features.append(feature)
            for child in feature.children.values():
                collect_pr_features(child)

        for root_feature in self.features.values():
            collect_pr_features(root_feature)

        return features

    def get_api_coverage(self) -> Dict[str, List[str]]:
        """Get a mapping of GitHub API endpoints to features."""
        api_to_features = {}

        def collect_apis(feature: OtterdogFeature):
            for operation, endpoints in feature.github_apis.items():
                for endpoint in endpoints:
                    key = f"{endpoint.method} {endpoint.path}"
                    if key not in api_to_features:
                        api_to_features[key] = []
                    api_to_features[key].append(feature.full_path)

            for child in feature.children.values():
                collect_apis(child)

        for root_feature in self.features.values():
            collect_apis(root_feature)

        return api_to_features