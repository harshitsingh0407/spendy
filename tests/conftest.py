import importlib
import sys

import pytest


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    """Point database.db.DB_PATH at a fresh sqlite file and seed it."""
    path = tmp_path / "test.db"
    import database.db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", str(path))
    db_module.init_db()
    db_module.seed_db()
    return path


@pytest.fixture()
def flask_app(db_path):
    """Import (or reload) app.py so its module-level init_db()/seed_db()
    calls run against the freshly-patched DB_PATH."""
    if "app" in sys.modules:
        app_module = importlib.reload(sys.modules["app"])
    else:
        app_module = importlib.import_module("app")
    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture()
def logged_in_client(client):
    from database.db import DEMO_USER

    client.post(
        "/login",
        data={"email": DEMO_USER["email"], "password": DEMO_USER["password"]},
    )
    return client
