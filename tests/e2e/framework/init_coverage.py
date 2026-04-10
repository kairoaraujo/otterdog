#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Coverage tracking for Otterdog init feature.

Provides comprehensive coverage metrics for the initialization process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class CoverageStatus(Enum):
    """Status of a coverage point."""
    NOT_TESTED = "not_tested"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class CoveragePoint:
    """Represents a single point of coverage."""

    id: str
    description: str
    category: str
    status: CoverageStatus = CoverageStatus.NOT_TESTED
    details: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    @property
    def is_covered(self) -> bool:
        """Check if this point is covered."""
        return self.status in (CoverageStatus.PASSED, CoverageStatus.PARTIAL)


@dataclass
class InitFeatureCoverage:
    """Track coverage for the Otterdog init feature."""

    def __init__(self):
        """Initialize coverage tracking."""
        self.coverage_points = self._define_coverage_points()
        self.test_results: Dict[str, CoverageStatus] = {}
        self.api_calls_made: Set[str] = set()
        self.database_operations: Set[str] = set()
        self.errors_encountered: List[str] = []

    def _define_coverage_points(self) -> Dict[str, CoveragePoint]:
        """Define all coverage points for init feature."""
        return {
            # Configuration Loading
            "config_fetch": CoveragePoint(
                "config_fetch",
                "Configuration fetched from repository",
                "configuration",
            ),
            "config_parse": CoveragePoint(
                "config_parse",
                "Configuration parsed successfully",
                "configuration",
                dependencies=["config_fetch"]
            ),
            "config_validate": CoveragePoint(
                "config_validate",
                "Configuration validated against schema",
                "configuration",
                dependencies=["config_parse"]
            ),

            # Policy Loading
            "policy_fetch": CoveragePoint(
                "policy_fetch",
                "Policies fetched from repository",
                "policy",
            ),
            "policy_parse": CoveragePoint(
                "policy_parse",
                "Policies parsed and loaded",
                "policy",
                dependencies=["policy_fetch"]
            ),
            "policy_apply": CoveragePoint(
                "policy_apply",
                "Policies applied to configuration",
                "policy",
                dependencies=["policy_parse"]
            ),

            # Blueprint Loading
            "blueprint_fetch": CoveragePoint(
                "blueprint_fetch",
                "Blueprints fetched from repository",
                "blueprint",
            ),
            "blueprint_parse": CoveragePoint(
                "blueprint_parse",
                "Blueprints parsed and loaded",
                "blueprint",
                dependencies=["blueprint_fetch"]
            ),

            # Installation Management
            "installation_create": CoveragePoint(
                "installation_create",
                "New installations created",
                "installation",
            ),
            "installation_update": CoveragePoint(
                "installation_update",
                "Existing installations updated",
                "installation",
            ),
            "installation_remove": CoveragePoint(
                "installation_remove",
                "Obsolete installations removed",
                "installation",
            ),

            # Organization Sync
            "org_fetch": CoveragePoint(
                "org_fetch",
                "Organization data fetched from GitHub",
                "sync",
            ),
            "org_store": CoveragePoint(
                "org_store",
                "Organization data stored in database",
                "sync",
                dependencies=["org_fetch"]
            ),
            "repo_fetch": CoveragePoint(
                "repo_fetch",
                "Repository data fetched from GitHub",
                "sync",
            ),
            "repo_store": CoveragePoint(
                "repo_store",
                "Repository data stored in database",
                "sync",
                dependencies=["repo_fetch"]
            ),
            "team_fetch": CoveragePoint(
                "team_fetch",
                "Team data fetched from GitHub",
                "sync",
            ),
            "team_store": CoveragePoint(
                "team_store",
                "Team data stored in database",
                "sync",
                dependencies=["team_fetch"]
            ),

            # Error Handling
            "error_config_missing": CoveragePoint(
                "error_config_missing",
                "Handles missing configuration gracefully",
                "error_handling",
            ),
            "error_github_api": CoveragePoint(
                "error_github_api",
                "Handles GitHub API errors",
                "error_handling",
            ),
            "error_database": CoveragePoint(
                "error_database",
                "Handles database errors",
                "error_handling",
            ),
            "error_partial_sync": CoveragePoint(
                "error_partial_sync",
                "Handles partial sync failures",
                "error_handling",
            ),

            # Idempotency
            "idempotent_config": CoveragePoint(
                "idempotent_config",
                "Configuration refresh is idempotent",
                "idempotency",
            ),
            "idempotent_sync": CoveragePoint(
                "idempotent_sync",
                "Organization sync is idempotent",
                "idempotency",
            ),
            "idempotent_install": CoveragePoint(
                "idempotent_install",
                "Installation update is idempotent",
                "idempotency",
            ),
        }

    def mark_covered(self, point_id: str, status: CoverageStatus = CoverageStatus.PASSED, details: str = None):
        """Mark a coverage point as covered."""
        if point_id in self.coverage_points:
            point = self.coverage_points[point_id]
            point.status = status
            if details:
                point.details = details
            self.test_results[point_id] = status

    def record_api_call(self, method: str, path: str):
        """Record an API call that was made."""
        self.api_calls_made.add(f"{method} {path}")

    def record_database_operation(self, collection: str, operation: str):
        """Record a database operation."""
        self.database_operations.add(f"{collection}.{operation}")

    def record_error(self, error: str):
        """Record an error encountered during testing."""
        self.errors_encountered.append(error)

    def get_coverage_by_category(self) -> Dict[str, Dict[str, int]]:
        """Get coverage statistics grouped by category."""
        categories = {}

        for point in self.coverage_points.values():
            if point.category not in categories:
                categories[point.category] = {
                    "total": 0,
                    "covered": 0,
                    "passed": 0,
                    "failed": 0,
                    "partial": 0,
                    "skipped": 0,
                }

            stats = categories[point.category]
            stats["total"] += 1

            if point.is_covered:
                stats["covered"] += 1

            if point.status == CoverageStatus.PASSED:
                stats["passed"] += 1
            elif point.status == CoverageStatus.FAILED:
                stats["failed"] += 1
            elif point.status == CoverageStatus.PARTIAL:
                stats["partial"] += 1
            elif point.status == CoverageStatus.SKIPPED:
                stats["skipped"] += 1

        return categories

    def get_overall_coverage(self) -> Dict[str, float]:
        """Get overall coverage statistics."""
        total = len(self.coverage_points)
        covered = sum(1 for p in self.coverage_points.values() if p.is_covered)
        passed = sum(1 for p in self.coverage_points.values() if p.status == CoverageStatus.PASSED)

        return {
            "total_points": total,
            "covered_points": covered,
            "passed_points": passed,
            "coverage_percentage": (covered / total * 100) if total > 0 else 0,
            "success_rate": (passed / covered * 100) if covered > 0 else 0,
        }

    def get_uncovered_points(self) -> List[CoveragePoint]:
        """Get list of uncovered points."""
        return [
            point for point in self.coverage_points.values()
            if point.status == CoverageStatus.NOT_TESTED
        ]

    def generate_report(self) -> str:
        """Generate a coverage report."""
        overall = self.get_overall_coverage()
        by_category = self.get_coverage_by_category()
        uncovered = self.get_uncovered_points()

        report = ["=" * 60]
        report.append("OTTERDOG INIT FEATURE COVERAGE REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall Statistics
        report.append("Overall Coverage:")
        report.append(f"  Total Points: {overall['total_points']}")
        report.append(f"  Covered: {overall['covered_points']} ({overall['coverage_percentage']:.1f}%)")
        report.append(f"  Passed: {overall['passed_points']} ({overall['success_rate']:.1f}% of covered)")
        report.append("")

        # Coverage by Category
        report.append("Coverage by Category:")
        for category, stats in sorted(by_category.items()):
            coverage_pct = (stats['covered'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report.append(f"  {category}:")
            report.append(f"    Total: {stats['total']}, Covered: {stats['covered']} ({coverage_pct:.1f}%)")
            report.append(f"    Passed: {stats['passed']}, Failed: {stats['failed']}, Partial: {stats['partial']}")
        report.append("")

        # API Coverage
        if self.api_calls_made:
            report.append(f"API Calls Made ({len(self.api_calls_made)}):")
            for call in sorted(self.api_calls_made):
                report.append(f"  - {call}")
            report.append("")

        # Database Operations
        if self.database_operations:
            report.append(f"Database Operations ({len(self.database_operations)}):")
            for op in sorted(self.database_operations):
                report.append(f"  - {op}")
            report.append("")

        # Uncovered Points
        if uncovered:
            report.append(f"Uncovered Points ({len(uncovered)}):")
            for point in uncovered:
                deps = f" (depends on: {', '.join(point.dependencies)})" if point.dependencies else ""
                report.append(f"  - [{point.category}] {point.id}: {point.description}{deps}")
            report.append("")

        # Errors
        if self.errors_encountered:
            report.append(f"Errors Encountered ({len(self.errors_encountered)}):")
            for error in self.errors_encountered:
                report.append(f"  - {error}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)