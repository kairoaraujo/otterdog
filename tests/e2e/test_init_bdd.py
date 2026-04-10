#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
BDD tests for Otterdog init feature.

Run with: pytest tests/e2e/test_init_bdd.py -v
"""

import pytest
from pytest_bdd import scenarios

# Import step definitions
from tests.e2e.steps.test_init_steps import *
# Import fixtures
from tests.e2e.fixtures.wiremock import wiremock_sync

# This automatically loads all scenarios from the feature file
# Each scenario becomes a test that engineers can run
scenarios('features/bdd/init.feature')


# Engineers can also add custom hooks for specific scenarios
@pytest.mark.usefixtures('wiremock_client', 'github_provider')
class TestOtterdogInit:
    """Test class for Otterdog initialization scenarios."""

    def test_coverage_report(self, bdd_context):
        """Generate coverage report after running scenarios."""
        # This runs after all BDD scenarios
        report = bdd_context.coverage_tracker.generate_report()
        print("\n" + report)

        # Could also save to file
        with open("coverage_report.txt", "w") as f:
            f.write(report)