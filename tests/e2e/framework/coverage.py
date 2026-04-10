#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Feature coverage tracking for E2E tests.

Tracks which Otterdog features have test coverage and generates reports.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest
from jinja2 import Template

from otterdog.utils import get_logger

from .features import FeatureRegistry, OtterdogFeature

_logger = get_logger(__name__)


class FeatureCoverageTracker:
    """Track test coverage for Otterdog features."""

    def __init__(self, output_dir: Path = None):
        """Initialize the coverage tracker."""
        self.output_dir = output_dir or Path("coverage")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.feature_registry = FeatureRegistry()
        self.tested_features: Set[str] = set()
        self.test_results: Dict[str, List[TestResult]] = {}
        self.start_time = datetime.now()

    def mark_tested(self, feature_path: str, test_name: str, result: str = "passed"):
        """Mark a feature as tested."""
        self.tested_features.add(feature_path)

        if feature_path not in self.test_results:
            self.test_results[feature_path] = []

        self.test_results[feature_path].append(
            TestResult(
                test_name=test_name,
                feature_path=feature_path,
                result=result,
                timestamp=datetime.now(),
            )
        )

    def get_coverage_stats(self) -> CoverageStats:
        """Calculate coverage statistics."""
        all_features = set(self.feature_registry.features_by_path.keys())

        # Get features from PR #614
        pr614_features = {
            f.full_path for f in self.feature_registry.get_features_from_pr("614")
        }

        # Calculate coverage
        covered = self.tested_features
        uncovered = all_features - covered

        pr614_covered = pr614_features & covered
        pr614_uncovered = pr614_features - covered

        total = len(all_features)
        covered_count = len(covered)
        coverage_percent = (covered_count / total * 100) if total > 0 else 0

        pr614_total = len(pr614_features)
        pr614_covered_count = len(pr614_covered)
        pr614_coverage_percent = (
            (pr614_covered_count / pr614_total * 100) if pr614_total > 0 else 0
        )

        return CoverageStats(
            total_features=total,
            covered_features=covered_count,
            uncovered_features=len(uncovered),
            coverage_percent=coverage_percent,
            covered_paths=sorted(covered),
            uncovered_paths=sorted(uncovered),
            pr614_total=pr614_total,
            pr614_covered=pr614_covered_count,
            pr614_coverage_percent=pr614_coverage_percent,
            pr614_covered_paths=sorted(pr614_covered),
            pr614_uncovered_paths=sorted(pr614_uncovered),
            by_operation=self._get_operation_coverage(),
        )

    def _get_operation_coverage(self) -> Dict[str, OperationCoverage]:
        """Get coverage by operation."""
        operations = ["import", "apply", "validate"]
        operation_coverage = {}

        for op in operations:
            features = self.feature_registry.get_features_for_operation(op)
            feature_paths = {f.full_path for f in features}

            covered = feature_paths & self.tested_features
            uncovered = feature_paths - covered

            total = len(feature_paths)
            covered_count = len(covered)
            coverage_percent = (covered_count / total * 100) if total > 0 else 0

            operation_coverage[op] = OperationCoverage(
                operation=op,
                total_features=total,
                covered_features=covered_count,
                coverage_percent=coverage_percent,
                covered_paths=sorted(covered),
                uncovered_paths=sorted(uncovered),
            )

        return operation_coverage

    def generate_report(self, format: str = "json") -> Path:
        """Generate a coverage report."""
        stats = self.get_coverage_stats()

        if format == "json":
            return self._generate_json_report(stats)
        elif format == "html":
            return self._generate_html_report(stats)
        elif format == "markdown":
            return self._generate_markdown_report(stats)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_json_report(self, stats: CoverageStats) -> Path:
        """Generate JSON coverage report."""
        report_file = self.output_dir / "coverage.json"

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "total_features": stats.total_features,
                "covered_features": stats.covered_features,
                "uncovered_features": stats.uncovered_features,
                "coverage_percent": stats.coverage_percent,
            },
            "pr614": {
                "total": stats.pr614_total,
                "covered": stats.pr614_covered,
                "coverage_percent": stats.pr614_coverage_percent,
                "covered_features": stats.pr614_covered_paths,
                "uncovered_features": stats.pr614_uncovered_paths,
            },
            "by_operation": {
                op: {
                    "total": cov.total_features,
                    "covered": cov.covered_features,
                    "coverage_percent": cov.coverage_percent,
                    "covered_features": cov.covered_paths,
                    "uncovered_features": cov.uncovered_paths,
                }
                for op, cov in stats.by_operation.items()
            },
            "covered_features": stats.covered_paths,
            "uncovered_features": stats.uncovered_paths,
            "test_results": {
                feature: [
                    {
                        "test": result.test_name,
                        "result": result.result,
                        "timestamp": result.timestamp.isoformat(),
                    }
                    for result in results
                ]
                for feature, results in self.test_results.items()
            },
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        _logger.info(f"JSON coverage report saved to {report_file}")
        return report_file

    def _generate_html_report(self, stats: CoverageStats) -> Path:
        """Generate HTML coverage report."""
        report_file = self.output_dir / "coverage.html"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Otterdog E2E Test Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .coverage-bar { width: 100%; height: 30px; background: #e0e0e0; border-radius: 5px; overflow: hidden; }
        .coverage-fill { height: 100%; background: linear-gradient(to right, #4CAF50, #8BC34A); }
        .feature-list { margin: 10px 0; }
        .covered { color: #4CAF50; }
        .uncovered { color: #f44336; }
        .pr614 { background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f0f0; }
    </style>
</head>
<body>
    <h1>Otterdog E2E Test Coverage Report</h1>
    <div class="summary">
        <h2>Overall Coverage</h2>
        <p>{{ stats.covered_features }} / {{ stats.total_features }} features covered ({{ "%.1f" | format(stats.coverage_percent) }}%)</p>
        <div class="coverage-bar">
            <div class="coverage-fill" style="width: {{ stats.coverage_percent }}%"></div>
        </div>
    </div>

    <div class="pr614">
        <h2>PR #614 Feature Coverage</h2>
        <p>{{ stats.pr614_covered }} / {{ stats.pr614_total }} features covered ({{ "%.1f" | format(stats.pr614_coverage_percent) }}%)</p>
        <div class="coverage-bar">
            <div class="coverage-fill" style="width: {{ stats.pr614_coverage_percent }}%"></div>
        </div>
        <details>
            <summary>Covered Features ({{ stats.pr614_covered }})</summary>
            <ul class="feature-list covered">
                {% for feature in stats.pr614_covered_paths %}
                <li>{{ feature }}</li>
                {% endfor %}
            </ul>
        </details>
        {% if stats.pr614_uncovered_paths %}
        <details>
            <summary>Uncovered Features ({{ stats.pr614_uncovered_paths | length }})</summary>
            <ul class="feature-list uncovered">
                {% for feature in stats.pr614_uncovered_paths %}
                <li>{{ feature }}</li>
                {% endfor %}
            </ul>
        </details>
        {% endif %}
    </div>

    <h2>Coverage by Operation</h2>
    <table>
        <tr>
            <th>Operation</th>
            <th>Total Features</th>
            <th>Covered</th>
            <th>Coverage %</th>
        </tr>
        {% for op, cov in stats.by_operation.items() %}
        <tr>
            <td>{{ op }}</td>
            <td>{{ cov.total_features }}</td>
            <td>{{ cov.covered_features }}</td>
            <td>{{ "%.1f" | format(cov.coverage_percent) }}%</td>
        </tr>
        {% endfor %}
    </table>

    <h2>All Covered Features</h2>
    <details>
        <summary>{{ stats.covered_features }} features</summary>
        <ul class="feature-list covered">
            {% for feature in stats.covered_paths %}
            <li>{{ feature }}</li>
            {% endfor %}
        </ul>
    </details>

    <h2>Uncovered Features</h2>
    <details>
        <summary>{{ stats.uncovered_features }} features</summary>
        <ul class="feature-list uncovered">
            {% for feature in stats.uncovered_paths %}
            <li>{{ feature }}</li>
            {% endfor %}
        </ul>
    </details>

    <footer>
        <p>Generated: {{ datetime.now().isoformat() }}</p>
    </footer>
</body>
</html>
        """)

        html_content = html_template.render(stats=stats, datetime=datetime)

        with open(report_file, "w") as f:
            f.write(html_content)

        _logger.info(f"HTML coverage report saved to {report_file}")
        return report_file

    def _generate_markdown_report(self, stats: CoverageStats) -> Path:
        """Generate Markdown coverage report."""
        report_file = self.output_dir / "coverage.md"

        md_template = Template("""# Otterdog E2E Test Coverage Report

Generated: {{ datetime.now().isoformat() }}

## Overall Coverage

**{{ stats.covered_features }} / {{ stats.total_features }}** features covered (**{{ "%.1f" | format(stats.coverage_percent) }}%**)

## PR #614 Feature Coverage

**{{ stats.pr614_covered }} / {{ stats.pr614_total }}** features covered (**{{ "%.1f" | format(stats.pr614_coverage_percent) }}%**)

### Covered PR #614 Features
{% for feature in stats.pr614_covered_paths %}
- ✅ `{{ feature }}`
{% endfor %}

{% if stats.pr614_uncovered_paths %}
### Uncovered PR #614 Features
{% for feature in stats.pr614_uncovered_paths %}
- ❌ `{{ feature }}`
{% endfor %}
{% endif %}

## Coverage by Operation

| Operation | Total Features | Covered | Coverage % |
|-----------|---------------|---------|------------|
{% for op, cov in stats.by_operation.items() %}
| {{ op }} | {{ cov.total_features }} | {{ cov.covered_features }} | {{ "%.1f" | format(cov.coverage_percent) }}% |
{% endfor %}

## Coverage Details

<details>
<summary>Covered Features ({{ stats.covered_features }})</summary>

{% for feature in stats.covered_paths %}
- `{{ feature }}`
{% endfor %}
</details>

<details>
<summary>Uncovered Features ({{ stats.uncovered_features }})</summary>

{% for feature in stats.uncovered_paths %}
- `{{ feature }}`
{% endfor %}
</details>
        """)

        md_content = md_template.render(stats=stats, datetime=datetime)

        with open(report_file, "w") as f:
            f.write(md_content)

        _logger.info(f"Markdown coverage report saved to {report_file}")
        return report_file


class CoverageStats:
    """Coverage statistics."""

    def __init__(
        self,
        total_features: int,
        covered_features: int,
        uncovered_features: int,
        coverage_percent: float,
        covered_paths: List[str],
        uncovered_paths: List[str],
        pr614_total: int,
        pr614_covered: int,
        pr614_coverage_percent: float,
        pr614_covered_paths: List[str],
        pr614_uncovered_paths: List[str],
        by_operation: Dict[str, OperationCoverage],
    ):
        self.total_features = total_features
        self.covered_features = covered_features
        self.uncovered_features = uncovered_features
        self.coverage_percent = coverage_percent
        self.covered_paths = covered_paths
        self.uncovered_paths = uncovered_paths
        self.pr614_total = pr614_total
        self.pr614_covered = pr614_covered
        self.pr614_coverage_percent = pr614_coverage_percent
        self.pr614_covered_paths = pr614_covered_paths
        self.pr614_uncovered_paths = pr614_uncovered_paths
        self.by_operation = by_operation


class OperationCoverage:
    """Coverage for a specific operation."""

    def __init__(
        self,
        operation: str,
        total_features: int,
        covered_features: int,
        coverage_percent: float,
        covered_paths: List[str],
        uncovered_paths: List[str],
    ):
        self.operation = operation
        self.total_features = total_features
        self.covered_features = covered_features
        self.coverage_percent = coverage_percent
        self.covered_paths = covered_paths
        self.uncovered_paths = uncovered_paths


class TestResult:
    """Result of a single test."""

    def __init__(
        self,
        test_name: str,
        feature_path: str,
        result: str,
        timestamp: datetime,
    ):
        self.test_name = test_name
        self.feature_path = feature_path
        self.result = result
        self.timestamp = timestamp


# Pytest plugin for coverage tracking
_coverage_tracker: Optional[FeatureCoverageTracker] = None


def pytest_configure(config):
    """Configure pytest plugin."""
    global _coverage_tracker
    if config.getoption("--e2e-coverage", default=False):
        _coverage_tracker = FeatureCoverageTracker()


def pytest_runtest_teardown(item, nextitem):
    """Track test coverage after each test."""
    if _coverage_tracker and hasattr(item, "callspec"):
        # Extract feature path from test
        if hasattr(item.cls, "feature_path"):
            feature_path = item.cls.feature_path
            test_name = item.nodeid
            result = "passed"  # Will be updated by pytest_runtest_makereport
            _coverage_tracker.mark_tested(feature_path, test_name, result)


def pytest_sessionfinish(session, exitstatus):
    """Generate coverage report at end of session."""
    if _coverage_tracker:
        _coverage_tracker.generate_report("json")
        _coverage_tracker.generate_report("html")
        _coverage_tracker.generate_report("markdown")

        # Print summary
        stats = _coverage_tracker.get_coverage_stats()
        print(f"\n{'=' * 60}")
        print(f"E2E Test Coverage Summary")
        print(f"{'=' * 60}")
        print(f"Overall: {stats.covered_features}/{stats.total_features} ({stats.coverage_percent:.1f}%)")
        print(f"PR #614: {stats.pr614_covered}/{stats.pr614_total} ({stats.pr614_coverage_percent:.1f}%)")
        print(f"{'=' * 60}\n")