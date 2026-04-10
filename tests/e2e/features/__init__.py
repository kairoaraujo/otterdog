#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""E2E tests for specific Otterdog features."""

from .test_env_secrets import TestEnvironmentSecrets
from .test_env_variables import TestEnvironmentVariables
from .test_dependabot_secrets import TestDependabotSecrets

__all__ = [
    "TestEnvironmentSecrets",
    "TestEnvironmentVariables",
    "TestDependabotSecrets",
]