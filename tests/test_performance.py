"""Response time tests — verify each route responds within an acceptable time.

Tests are generated dynamically from the app's feature/overall/db_options
definitions so they expand automatically as the code grows.

Run:    pytest tests/test_performance.py -v
Skip:   pytest tests/ -m "not slow"
"""

import time
import pytest

from web.settings import features, overall, phenomena, DEFAULT_DB_OPTION
from web.db import db_options


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _switch_db(client, db):
    """POST to /settings to switch the active database."""
    client.post('/settings', data={
        'color_palette': 'purple_orange',
        'db_option': db,
    })


def _timed_get(client, url):
    """GET a URL and return (response, elapsed_seconds)."""
    start = time.time()
    resp = client.get(url)
    elapsed = time.time() - start
    return resp, elapsed


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fresh(app):
    """Per-test client so session state doesn't leak between tests."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Parameter generation — pulled from the live code
# ---------------------------------------------------------------------------

def _db_ids():
    """All db_option keys."""
    return list(db_options.keys())


def _feature_params():
    """(db, f1, f2, label) for every valid feature × database combo."""
    params = []
    for f1, f2, name, possible in features:
        for db in possible:
            label = f"{db}/{name}"
            params.append(pytest.param(db, f1, f2, id=label))
    return params


def _overall_params():
    """(db, f1, f2, label) for every valid overall × database combo."""
    params = []
    for f1, f2, name, possible in overall:
        for db in possible:
            label = f"{db}/{name}"
            params.append(pytest.param(db, f1, f2, id=label))
    return params


# ---------------------------------------------------------------------------
# 1. Static / JSON-backed pages (no DB switch needed, fast)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("url,max_seconds", [
    ('/', 2),
    ('/phenomena/diversity.html', 2),
    ('/phenomena/androgyny.html', 2),
    ('/overlap.html', 2),
    ('/phenomena/topnames.html', 2),
    ('/genderedness.html', 2),
    ('/phenomena/jinmeiyou.html', 2),
    ('/phenomena/redup.html', 5),
])
def test_static_routes(client, url, max_seconds):
    resp, elapsed = _timed_get(client, url)
    assert resp.status_code == 200
    assert elapsed < max_seconds, f"{url} took {elapsed:.1f}s (max {max_seconds}s)"


# ---------------------------------------------------------------------------
# 2. Per-database pages: stats, names, years, irregular, kanji
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("db", _db_ids())
def test_stats_page(fresh, db):
    _switch_db(fresh, db)
    resp, elapsed = _timed_get(fresh, '/stats.html')
    assert resp.status_code == 200
    assert elapsed < 10, f"/stats.html [{db}] took {elapsed:.1f}s"


@pytest.mark.slow
@pytest.mark.parametrize("db", _db_ids())
def test_names_page(fresh, db):
    _switch_db(fresh, db)
    resp, elapsed = _timed_get(fresh, '/names.html')
    assert resp.status_code == 200
    assert elapsed < 25, f"/names.html [{db}] took {elapsed:.1f}s"


@pytest.mark.slow
@pytest.mark.parametrize("db", _db_ids())
def test_years_page(fresh, db):
    _switch_db(fresh, db)
    resp, elapsed = _timed_get(fresh, '/years.html')
    assert resp.status_code == 200
    assert elapsed < 5, f"/years.html [{db}] took {elapsed:.1f}s"


@pytest.mark.slow
@pytest.mark.parametrize("db", _db_ids())
def test_irregular_page(fresh, db):
    _switch_db(fresh, db)
    resp, elapsed = _timed_get(fresh, '/irregular.html')
    assert resp.status_code == 200
    assert elapsed < 10, f"/irregular.html [{db}] took {elapsed:.1f}s"


@pytest.mark.slow
@pytest.mark.parametrize("db", _db_ids())
def test_kanji_page(fresh, db):
    _switch_db(fresh, db)
    resp, elapsed = _timed_get(fresh, '/kanji?kanji=美')
    assert resp.status_code == 200
    assert elapsed < 5, f"/kanji [{db}] took {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# 3. Feature pages — every feature × compatible database
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("db,f1,f2", _feature_params())
def test_feature_page(fresh, db, f1, f2):
    _switch_db(fresh, db)
    url = f'/features.html?f1={f1}&f2={f2}&nm=test'
    resp, elapsed = _timed_get(fresh, url)
    assert resp.status_code == 200
    assert elapsed < 10, f"{url} [{db}] took {elapsed:.1f}s"


# ---------------------------------------------------------------------------
# 4. Overall pages — every overall × compatible database
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("db,f1,f2", _overall_params())
def test_overall_page(fresh, db, f1, f2):
    _switch_db(fresh, db)
    url = f'/features.html?f1={f1}&f2={f2}&nm=test'
    resp, elapsed = _timed_get(fresh, url)
    assert resp.status_code == 200
    assert elapsed < 10, f"{url} [{db}] took {elapsed:.1f}s"
