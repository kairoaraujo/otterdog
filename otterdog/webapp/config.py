#  *******************************************************************************
#  Copyright (c) 2023-2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

import os
import secrets

from decouple import config  # type: ignore


class AppConfig:
    QUART_APP = "otterdog.webapp"

    BASE_URL = config("BASE_URL")

    # Assets Management
    ASSETS_ROOT = config("ASSETS_ROOT", default="/static/assets")

    CACHE_CONTROL = config("CACHE_CONTROL", default=False)

    APP_ROOT = config("APP_ROOT")
    DB_ROOT = os.path.join(APP_ROOT, "db")

    MONGO_URI = config("MONGO_URI", default="mongodb://mongodb:27017/otterdog")
    REDIS_URI = config("REDIS_URI", default="redis://redis:6379")
    GHPROXY_URI = config("GHPROXY_URI", default="http://ghproxy:8888")

    OTTERDOG_CONFIG_OWNER = config("OTTERDOG_CONFIG_OWNER", default=None)
    OTTERDOG_CONFIG_REPO = config("OTTERDOG_CONFIG_REPO", default=None)
    OTTERDOG_CONFIG_PATH = config("OTTERDOG_CONFIG_PATH", default=None)
    OTTERDOG_CONFIG_TOKEN = config("OTTERDOG_CONFIG_TOKEN", default=None)

    # Set up the App SECRET_KEY
    SECRET_KEY = config("SECRET_KEY", default=None)
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(16)

    GITHUB_ADMIN_TEAMS = config("GITHUB_ADMIN_TEAMS", default="otterdog-admins")
    GITHUB_WEBHOOK_ENDPOINT = config("GITHUB_WEBHOOK_ENDPOINT", default="/github-webhook/receive")
    GITHUB_WEBHOOK_SECRET = config("GITHUB_WEBHOOK_SECRET", default=None)
    GITHUB_WEBHOOK_VALIDATION_CONTEXT = config("GITHUB_WEBHOOK_VALIDATION_CONTEXT", default="otterdog-validate")
    GITHUB_WEBHOOK_SYNC_CONTEXT = config("GITHUB_WEBHOOK_SYNC_CONTEXT", default="otterdog-sync")

    # GitHub OAuth config
    GITHUB_CLIENT_ID = config("GITHUB_OAUTH_CLIENT_ID", default=None)
    GITHUB_CLIENT_SECRET = config("GITHUB_OAUTH_CLIENT_SECRET", default=None)

    # GitHub App config
    GITHUB_APP_ID = config("GITHUB_APP_ID")
    GITHUB_APP_PRIVATE_KEY = config("GITHUB_APP_PRIVATE_KEY")

    PROJECTS_BASE_URL = config("PROJECTS_BASE_URL", default="https://projects.eclipse.org/projects/")
    DEPENDENCY_TRACK_URL = config("DEPENDENCY_TRACK_URL")
    DEPENDENCY_TRACK_TOKEN = config("DEPENDENCY_TRACK_TOKEN")


class ProductionConfig(AppConfig):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class DebugConfig(AppConfig):
    DEBUG = True

    TEMPLATES_AUTO_RELOAD = True


class TestingConfig(AppConfig):
    TESTING = True

    APP_ROOT = "./approot"
    DB_ROOT = os.path.join(APP_ROOT, "db")

    MONGO_URI = "mongodb://localhost:27017/otterdog"


# Load all possible configurations
config_dict = {"Production": ProductionConfig, "Debug": DebugConfig}
