#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""E2E tests for Otterdog operations."""

from .test_import import TestImportOperation
from .test_apply import TestApplyOperation
from .test_validate import TestValidateOperation

__all__ = [
    "TestImportOperation",
    "TestApplyOperation",
    "TestValidateOperation",
]