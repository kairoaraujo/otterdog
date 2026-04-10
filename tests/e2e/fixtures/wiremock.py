#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""
WireMock fixtures for E2E testing.
"""

import asyncio
import json
from typing import Any, Dict

import aiohttp
import pytest


class WireMockClient:
    """Client for interacting with WireMock."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize WireMock client."""
        self.base_url = base_url
        self.admin_url = f"{base_url}/__admin"

    async def reset(self):
        """Reset all stubs and request logs."""
        async with aiohttp.ClientSession() as session:
            await session.post(f"{self.admin_url}/reset")

    async def stub_for(self, mapping: Dict[str, Any]):
        """Create a stub mapping."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.admin_url}/mappings",
                json=mapping,
                headers={"Content-Type": "application/json"}
            ) as response:
                return await response.json()

    async def verify(self, method: str, url: str, times: int = 1):
        """Verify a request was made."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.admin_url}/requests/count",
                json={
                    "method": method,
                    "url": url
                }
            ) as response:
                result = await response.json()
                return result.get("count", 0) == times

    async def get_requests(self):
        """Get all received requests."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.admin_url}/requests") as response:
                return await response.json()

    async def setup_github_api_mocks(self):
        """Set up common GitHub API mocks."""
        # Mock GitHub API rate limit
        await self.stub_for({
            "request": {
                "method": "GET",
                "urlPath": "/rate_limit"
            },
            "response": {
                "status": 200,
                "jsonBody": {
                    "resources": {
                        "core": {
                            "limit": 5000,
                            "remaining": 4999,
                            "reset": 1635724800
                        }
                    }
                }
            }
        })

        # Mock organization endpoint
        await self.stub_for({
            "request": {
                "method": "GET",
                "urlPathPattern": "/orgs/([^/]+)"
            },
            "response": {
                "status": 200,
                "jsonBody": {
                    "login": "test-org",
                    "id": 12345678,
                    "name": "Test Organization",
                    "billing_email": "admin@test.org",
                    "default_repository_permission": "read",
                    "members_can_create_repositories": True,
                    "two_factor_requirement_enabled": True,
                    "web_commit_signoff_required": False
                }
            }
        })

        # Mock repositories list
        await self.stub_for({
            "request": {
                "method": "GET",
                "urlPathPattern": "/orgs/([^/]+)/repos"
            },
            "response": {
                "status": 200,
                "jsonBody": [
                    {
                        "id": 1,
                        "name": "test-repo",
                        "full_name": "test-org/test-repo",
                        "private": False,
                        "description": "Test repository"
                    }
                ]
            }
        })

        # Mock teams list
        await self.stub_for({
            "request": {
                "method": "GET",
                "urlPathPattern": "/orgs/([^/]+)/teams"
            },
            "response": {
                "status": 200,
                "jsonBody": [
                    {
                        "id": 1,
                        "name": "developers",
                        "slug": "developers",
                        "description": "Development team",
                        "permission": "push"
                    }
                ]
            }
        })


@pytest.fixture
async def wiremock():
    """Provide WireMock client for tests."""
    client = WireMockClient()

    # Reset WireMock before each test
    await client.reset()

    # Set up common GitHub API mocks
    await client.setup_github_api_mocks()

    yield client

    # Clean up after test
    await client.reset()


@pytest.fixture
def wiremock_sync():
    """Provide synchronous WireMock client for BDD tests."""
    client = WireMockClient()

    # Run async operations synchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Reset and setup
    loop.run_until_complete(client.reset())
    loop.run_until_complete(client.setup_github_api_mocks())

    # Wrap async methods for sync use
    class SyncWireMockClient:
        def __init__(self, async_client, loop):
            self.async_client = async_client
            self.loop = loop

        def stub_for(self, mapping):
            return self.loop.run_until_complete(self.async_client.stub_for(mapping))

        def verify(self, method, url, times=1):
            return self.loop.run_until_complete(self.async_client.verify(method, url, times))

        def get_requests(self):
            return self.loop.run_until_complete(self.async_client.get_requests())

        def reset(self):
            return self.loop.run_until_complete(self.async_client.reset())

    yield SyncWireMockClient(client, loop)

    # Clean up
    loop.run_until_complete(client.reset())
    loop.close()