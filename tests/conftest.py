"""Shared fixtures for the test suite.

Requires a built database at web/db/namae.db — these are integration
tests against the real data, not unit tests with mocked fixtures.
"""

import os
import sys
import pytest

# Add repo root to sys.path so that `import web` works regardless of
# how pytest is invoked.
_repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, _repo_root)

# Ensure the working directory is the repo root so that relative paths
# used by the app (e.g. repo_root, data/) resolve correctly.
os.chdir(_repo_root)


@pytest.fixture(scope='session')
def app():
    from web import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture()
def client_fresh(app):
    """A per-test client with a fresh session (no cookies carried over)."""
    return app.test_client()
