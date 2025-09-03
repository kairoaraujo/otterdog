#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************


import pytest

from otterdog.webapp.tasks.merge_pull_request import MergePullRequestTask


class TestMergePullRequestTaskExecute:
    @pytest.mark.asyncio
    async def test_task__execute(self):
        task = MergePullRequestTask(
            installation_id=1,
            org_id="test-org",
            repo_name="test-repo",
            pull_request_number=1,
            author="test-author",
        )
        assert await task.execute() is None
