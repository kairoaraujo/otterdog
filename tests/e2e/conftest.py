#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
Pytest configuration for E2E tests.
"""

import asyncio
import json
import os
from pathlib import Path

import pytest
import pytest_asyncio

from otterdog.credentials import Credentials
from otterdog.providers.github import GitHubProvider


class MockWireMock:
    """Mock WireMock server for testing."""

    def __init__(self):
        self.stubs = []
        self.requests = []

    async def stub_for(self, stub):
        """Add a stub mapping."""
        self.stubs.append(stub)

    async def get_requests(self):
        """Get recorded requests."""
        return self.requests

    async def reset(self):
        """Reset all stubs and requests."""
        self.stubs.clear()
        self.requests.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def wiremock():
    """Mock WireMock server."""
    mock = MockWireMock()
    yield mock
    await mock.reset()


@pytest_asyncio.fixture
async def github_provider():
    """Create GitHub provider for testing."""
    credentials = Credentials(
        _username="test-user",
        _password="test-pass",
        _totp_secret="test-totp",
        _github_token="test-token",
    )

    # Override API URL if WireMock is running
    if os.environ.get("E2E_TESTING"):
        os.environ["GITHUB_API_URL"] = "http://localhost:8080"

    provider = GitHubProvider(credentials)
    yield provider
    await provider.close()


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory for test files."""
    return tmp_path_factory.mktemp("e2e_test")


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "operation: mark test for specific operation")
    config.addinivalue_line("markers", "feature: mark test for specific feature")
    config.addinivalue_line("markers", "pr614: mark test for PR #614 features")