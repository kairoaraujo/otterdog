#  *******************************************************************************
#  Copyright (c) 2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

"""E2E testing framework core components."""

from .base import OtterdogE2ETest, OtterdogFeatureTest, OtterdogOperationTest
from .features import FeatureRegistry
from .coverage import FeatureCoverageTracker

__all__ = [
    "OtterdogE2ETest",
    "OtterdogFeatureTest",
    "OtterdogOperationTest",
    "FeatureRegistry",
    "FeatureCoverageTracker",
]