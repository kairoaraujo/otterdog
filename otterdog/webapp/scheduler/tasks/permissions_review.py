#  *******************************************************************************
#  Copyright (c) 2024-2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from otterdog.models.github_organization import GitHubOrganization
from otterdog.webapp import mongo
from otterdog.webapp.db.models import (
    InstallationStatus,
    PermissionsReviewId,
    PermissionsReviewStatus,
    PermissionsReviewTrackingModel,
)
from otterdog.webapp.db.service import (
    find_policy,
    get_configuration_by_github_id,
    get_installations,
)
from otterdog.webapp.policies import create_policy_from_model
from otterdog.webapp.utils import get_rest_api_for_installation

if TYPE_CHECKING:
    from quart import Quart

    from otterdog.models.repository import Repository
    from otterdog.providers.github.rest import RestApi
    from otterdog.webapp.db.models import InstallationModel
    from otterdog.webapp.policies.project_permissions_review import ProjectPermissionsReviewPolicy

logger = logging.getLogger(__name__)


async def run_permissions_review_check(app: Quart | None = None) -> None:
    """
    Main entry point for the scheduled permissions review task.
    This function is called by the scheduler.

    Args:
        app: Quart app instance (kept for compatibility with scheduler)
    """
    _ = app  # Not sure why this is needed, but keeping for compatibility
    logger.info("Starting scheduled permissions review check")

    try:
        organizations = await get_installations()
        processed_count = 0
        created_count = 0

        for org in organizations:
            if org.installation_status != InstallationStatus.INSTALLED:
                continue

            try:
                issues_created = await process_organization(org)
                created_count += issues_created
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing organization {org.github_id}: {e}", exc_info=True)

        logger.info(
            f"Permissions review check completed: "
            f"processed {processed_count} organizations, "
            f"created {created_count} review issues"
        )
    except Exception as e:
        logger.error(f"Fatal error in permissions review check: {e}", exc_info=True)


async def process_organization(org: InstallationModel) -> int:
    """Process a single organization for due permission reviews."""

    policy_model = await find_policy(org.github_id, "project_permissions_review")
    if not policy_model:
        logger.debug(f"No PPR policy found for organization {org.github_id}")
        return 0

    policy = create_policy_from_model(policy_model)

    from otterdog.webapp.policies.project_permissions_review import ProjectPermissionsReviewPolicy

    if not isinstance(policy, ProjectPermissionsReviewPolicy):
        return 0

    config = await get_configuration_by_github_id(org.github_id)
    if not config:
        logger.warning(f"No configuration found for organization {org.github_id}")
        return 0

    github_org = GitHubOrganization.from_model_data(config.config)

    rest_api = await get_rest_api_for_installation(org.installation_id)

    created_count = 0
    for repo in github_org.repositories:
        try:
            if await should_create_review(org.github_id, repo, policy):
                await create_review_issue(rest_api, org.github_id, repo, policy)
                created_count += 1
        except Exception as e:
            logger.error(f"Error processing repository {org.github_id}/{repo.name}: {e}", exc_info=True)

    return created_count


async def should_create_review(org_id: str, repo: Repository, policy: ProjectPermissionsReviewPolicy) -> bool:
    """Determine if a review issue should be created for this repository."""

    if not repo.has_issues:
        logger.debug(f"Skipping review for {org_id}/{repo.name}: issues disabled")
        return False

    review_frequency = repo.permissions_review_frequency

    if review_frequency == 0:
        logger.debug(f"Reviews disabled for {org_id}/{repo.name}")
        return False
    elif review_frequency is None:
        review_frequency = policy.review_frequency
        if not policy.enabled_by_default:
            logger.debug(f"Reviews disabled by org default for {org_id}/{repo.name}")
            return False

    tracking_id = PermissionsReviewId(org_id=org_id, repo_name=repo.name)

    tracking = await mongo.odm.find_one(
        PermissionsReviewTrackingModel, PermissionsReviewTrackingModel.id == tracking_id
    )

    now = datetime.now(UTC)

    if tracking is None:
        tracking = PermissionsReviewTrackingModel(
            id=tracking_id,
            review_frequency=review_frequency,
            next_review_date=now,
            status=PermissionsReviewStatus.PENDING,
        )
        await mongo.odm.save(tracking)
        logger.info(f"Created new tracking record for {org_id}/{repo.name}")
        return True

    next_review = tracking.next_review_date
    if next_review:
        if next_review.tzinfo is None:
            next_review = next_review.replace(tzinfo=UTC)

    if next_review and next_review <= now:
        # avoid duplicates
        if tracking.last_issue_created:
            last_created = tracking.last_issue_created
            if last_created.tzinfo is None:
                last_created = last_created.replace(tzinfo=UTC)
            days_since_last = (now - last_created).days
            if days_since_last < 7:  # TESTING IT
                logger.debug(f"Skipping review for {org_id}/{repo.name}: " f"issue created {days_since_last} days ago")
                return False
        logger.info(f"Review is due for {org_id}/{repo.name}")
        return True

    logger.debug(f"Review not due for {org_id}/{repo.name}. " f"Next review date: {tracking.next_review_date}")
    return False


async def create_review_issue(
    rest_api: RestApi, org_id: str, repo: Repository, policy: ProjectPermissionsReviewPolicy
) -> None:
    """Create a review issue and update tracking."""

    title = repo.permissions_review_title or policy.issue_title or "Periodic Review: Project Permissions"

    body = repo.permissions_review_body
    if not body:
        body = policy.get_issue_body(repo.name, org_id)

    try:
        issue = await rest_api.issue.create_issue(org_id, repo.name, title, body)

        logger.info(f"Created permissions review issue #{issue['number']} " f"for {org_id}/{repo.name}")

        tracking_id = PermissionsReviewId(org_id=org_id, repo_name=repo.name)

        tracking = await mongo.odm.find_one(
            PermissionsReviewTrackingModel, PermissionsReviewTrackingModel.id == tracking_id
        )

        if tracking:
            now = datetime.now(UTC)
            review_frequency = repo.permissions_review_frequency or policy.review_frequency

            tracking.last_issue_created = now
            tracking.last_issue_number = issue["number"]
            tracking.next_review_date = now + timedelta(days=30 * review_frequency)
            tracking.status = PermissionsReviewStatus.CREATED
            tracking.review_frequency = review_frequency
            tracking.custom_title = repo.permissions_review_title
            tracking.custom_body = repo.permissions_review_body

            await mongo.odm.save(tracking)
            logger.debug(f"Updated tracking for {org_id}/{repo.name}. " f"Next review: {tracking.next_review_date}")

    except Exception as e:
        logger.error(f"Failed to create review issue for {org_id}/{repo.name}: {e}", exc_info=True)

        tracking_id = PermissionsReviewId(org_id=org_id, repo_name=repo.name)

        tracking = await mongo.odm.find_one(
            PermissionsReviewTrackingModel, PermissionsReviewTrackingModel.id == tracking_id
        )

        if tracking:
            tracking.status = PermissionsReviewStatus.OVERDUE
            await mongo.odm.save(tracking)
