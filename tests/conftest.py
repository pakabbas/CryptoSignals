import os

import pytest

from app import create_app
from app.database import db


@pytest.fixture()
def app():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["TESTING"] = "true"
    os.environ["ENABLE_SCHEDULER"] = "false"
    application = create_app()
    application.config.update(
        {
            "TESTING": True,
            "LOG_TO_DATABASE": False,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
