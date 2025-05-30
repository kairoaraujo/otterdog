#  *******************************************************************************
#  Copyright (c) 2023-2025 Eclipse Foundation and others.
#  This program and the accompanying materials are made available
#  under the terms of the Eclipse Public License 2.0
#  which is available at http://www.eclipse.org/legal/epl-v20.html
#  SPDX-License-Identifier: EPL-2.0
#  *******************************************************************************

from __future__ import annotations

import json
import os
from datetime import datetime
from importlib import import_module
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any

import quart_flask_patch  # type: ignore # noqa: F401
from flask_github import GitHub  # type: ignore
from quart import Quart
from quart.json.provider import DefaultJSONProvider
from quart_auth import QuartAuth
from quart_redis import RedisHandler  # type: ignore

from otterdog.cache import set_github_cache

from .db import Mongo, init_mongo_database
from .filters import register_filters
from .utils import close_rest_apis, get_github_ghproxy_cache, get_temporary_base_directory

if TYPE_CHECKING:
    from .config import AppConfig

_BLUEPRINT_MODULES: list[str] = ["home", "api", "internal", "auth"]

mongo = Mongo()
redis_handler = RedisHandler()
auth_manager: QuartAuth | None = None
oauth_github: GitHub | None = None


def register_extensions(app):
    mongo.init_app(app)
    redis_handler.init_app(app)

    if app.config["GITHUB_CLIENT_ID"] is not None:
        from otterdog.webapp.auth import User

        global auth_manager
        global oauth_github

        auth_manager = QuartAuth(cookie_secure=False)  # type: ignore
        oauth_github = GitHub()

        auth_manager.user_class = User
        auth_manager.init_app(app)

        oauth_github.init_app(app)
    else:

        @app.context_processor
        async def dummy_user() -> dict[str, Any]:
            return {
                "current_user": None,
            }


def register_github_webhook(app) -> None:
    webhook_fqn = "otterdog.webapp.webhook"
    spec = find_spec(webhook_fqn)
    if spec is not None:
        module = import_module(webhook_fqn)
        module.webhook.init_app(app)


def register_blueprints(app):
    global auth_manager

    for module_name in _BLUEPRINT_MODULES:
        if module_name == "auth" and auth_manager is None:
            continue

        routes_fqn = f"otterdog.webapp.{module_name}.routes"
        spec = find_spec(routes_fqn)
        if spec is not None:
            module = import_module(routes_fqn)
            app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_serving
    async def configure():
        async with app.app_context():
            await init_mongo_database(mongo)


def create_app(app_config: AppConfig):
    app = Quart(
        app_config.QUART_APP,
        static_url_path="/assets",
        static_folder="static/assets",
    )
    app.config.from_object(app_config)

    manifest = {}
    manifest_path = os.path.join(app.root_path, "static/assets/manifest.json")
    try:
        with open(manifest_path) as content:
            manifest = json.load(content)
    except OSError as exception:
        raise RuntimeError(f"Manifest file not found at '{manifest_path}'. Run `npm run build`.") from exception

    @app.context_processor
    def context_processor():
        def asset(file_path):
            try:
                return f"/assets/{manifest[file_path]['file']}"
            except:  # noqa
                app.logger.error(f"did not find asset {file_path}")
                return f"/assets/{file_path}"

        return {"asset": asset}

    set_github_cache(get_github_ghproxy_cache(app.config))

    register_extensions(app)
    register_github_webhook(app)
    register_blueprints(app)
    configure_database(app)

    register_filters(app)

    class CustomJSONProvider(DefaultJSONProvider):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)

    app.json = CustomJSONProvider(app)

    @app.after_serving
    async def close_resources() -> None:
        from aioshutil import rmtree

        app.logger.info("shutting down app")

        await rmtree(get_temporary_base_directory(app))
        await close_rest_apis()

    return app
