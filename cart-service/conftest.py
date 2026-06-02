import os

import pytest

from app import create_app
from app.models import Base


@pytest.fixture(scope='session')
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    yield app
    app.extensions['db_engine'].dispose()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clear the database before each test."""
    engine = app.extensions['db_engine']
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client(app):
    return app.test_client()
