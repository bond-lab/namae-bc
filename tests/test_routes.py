"""Regression tests for all web routes.

Run with:  pytest tests/ -v
Requires:  web/db/namae.db (built via makedb.sh)
"""

import json
import pytest

from web.db import db_options
from web.settings import features, overall


# ---------------------------------------------------------------------------
# Per-model metadata
# ---------------------------------------------------------------------------

#: What each db option supports for search.
DB_CAPS = {
    'bc':      {'orth': True,  'pron': True,  'kanji': True},
    'hs':      {'orth': True,  'pron': False, 'kanji': True},
    'meiji':   {'orth': True,  'pron': False, 'kanji': True},
    'meiji_p': {'orth': False, 'pron': True,  'kanji': False},
}

#: A name that exists in every orth-supporting source.
SAMPLE_ORTH = '花'
#: A pronunciation that exists in bc and meiji_p.
SAMPLE_PRON = 'はな'
#: A kanji that exists in every orth-supporting source.
SAMPLE_KANJI = '花'


def _switch_db(client, db: str) -> None:
    """POST to /settings to switch the active database."""
    client.post('/settings', data={'color_palette': 'purple_orange', 'db_option': db})


# ── Helpers ──────────────────────────────────────────────────────────

def assert_html_ok(resp, status=200, must_contain=None, must_not_contain=None):
    """Assert response status and optional content checks."""
    assert resp.status_code == status, (
        f"Expected {status}, got {resp.status_code} for {resp.request.url}")
    if must_contain:
        html = resp.data.decode()
        for text in must_contain:
            assert text in html, f"Missing expected text: {text!r}"
    if must_not_contain:
        html = resp.data.decode()
        for text in must_not_contain:
            assert text not in html, f"Unexpected text found: {text!r}"


# ── Home / static pages ─────────────────────────────────────────────

class TestHome:
    def test_home_get(self, client):
        resp = client.get('/')
        assert_html_ok(resp, must_contain=['namae'])

    def test_home_post(self, client):
        resp = client.post('/')
        assert resp.status_code in (200, 302, 405)


class TestDocs:
    def test_docs_redirect(self, client):
        resp = client.get('/docs')
        assert resp.status_code in (301, 302, 308)

    def test_docs_data(self, client):
        resp = client.get('/docs/data.html')
        assert_html_ok(resp)

    def test_docs_download(self, client):
        resp = client.get('/docs/download.html')
        assert_html_ok(resp, must_contain=['download', '.tsv'])

    def test_docs_morae(self, client):
        resp = client.get('/docs/morae.html')
        assert_html_ok(resp)

    def test_docs_features(self, client):
        resp = client.get('/docs/features.html')
        assert_html_ok(resp)

    def test_docs_licenses(self, client):
        resp = client.get('/docs/licenses.html')
        assert_html_ok(resp)


class TestBook:
    def test_book_page(self, client):
        resp = client.get('/book')
        assert_html_ok(resp)


# ── Settings ─────────────────────────────────────────────────────────

class TestSettings:
    def test_settings_get(self, client_fresh):
        resp = client_fresh.get('/settings')
        assert_html_ok(resp, must_contain=['settings', 'color'])

    def test_settings_post_palette(self, client_fresh):
        resp = client_fresh.post('/settings', data={
            'color_palette': 'blue_red',
            'db_option': 'bc',
        }, follow_redirects=True)
        assert_html_ok(resp)

    def test_settings_post_db_option(self, client_fresh):
        resp = client_fresh.post('/settings', data={
            'color_palette': 'orange_purple',
            'db_option': 'meiji',
        }, follow_redirects=True)
        assert_html_ok(resp)


# ── Name search ──────────────────────────────────────────────────────

class TestNameSearch:
    def test_namae_no_params(self, client):
        """No params → search landing page."""
        resp = client.get('/namae')
        assert_html_ok(resp)

    def test_namae_orth_kanji(self, client):
        """Search by orthography (kanji)."""
        resp = client.get('/namae?orth=太郎')
        assert_html_ok(resp, must_contain=['太郎'])

    def test_namae_pron_hiragana(self, client):
        """Search by pronunciation (hiragana)."""
        resp = client.get('/namae?pron=はなこ')
        assert_html_ok(resp)

    def test_namae_invalid_pron(self, client):
        """Non-hiragana pronunciation → error, not crash."""
        resp = client.get('/namae?pron=abc')
        assert_html_ok(resp, must_contain=['hiragana'])

    def test_namae_invalid_orth(self, client):
        """Non-Japanese orthography → error, not crash."""
        resp = client.get('/namae?orth=abc')
        assert_html_ok(resp)

    def test_namae_orth_without_pron(self, client):
        """Kanji present in Heisei (NULL pron) must not crash with hira2roma.

        花 exists in Heisei with no pronunciation; previously this caused
        TypeError: expected string or bytes-like object, got 'NoneType'.
        """
        resp = client.get('/namae?orth=%E8%8A%B1&pron=')
        assert_html_ok(resp, must_contain=['花'])


# ── Kanji search ─────────────────────────────────────────────────────

class TestKanjiSearch:
    def test_kanji_no_params(self, client):
        resp = client.get('/kanji')
        assert_html_ok(resp)

    def test_kanji_valid(self, client):
        resp = client.get('/kanji?kanji=美')
        assert_html_ok(resp, must_contain=['美'])

    def test_kanji_invalid_multi_char(self, client):
        """Multiple characters → error, not crash."""
        resp = client.get('/kanji?kanji=美子')
        assert_html_ok(resp)

    def test_kanji_invalid_non_kanji(self, client):
        """Non-kanji → error, not crash."""
        resp = client.get('/kanji?kanji=a')
        assert_html_ok(resp)

    def test_kanji_glob_injection(self, client):
        """Special GLOB characters should not crash."""
        resp = client.get('/kanji?kanji=*')
        assert_html_ok(resp)

    def test_kanji_names_list_present(self, client):
        """Kanji page must include a list of names containing that kanji."""
        resp = client.get('/kanji?kanji=%E8%8A%B1')  # 花
        assert_html_ok(resp, must_contain=['Names containing', '花'])

    def test_kanji_names_link_to_namae(self, client):
        """Each name badge must link to the namae lookup page."""
        resp = client.get('/kanji?kanji=%E7%BF%94')  # 翔
        assert_html_ok(resp)
        html = resp.data.decode()
        assert '/namae?' in html, "Expected links to /namae? in names list"

    def test_kanji_no_names_no_crash(self, client):
        """A kanji with no names in the DB must not crash (empty names list)."""
        resp = client.get('/kanji?kanji=%E6%8B%B3')  # 拳 — unlikely in names
        assert_html_ok(resp)


# ── DB-dependent list pages ──────────────────────────────────────────

class TestNames:
    def test_names_page(self, client):
        resp = client.get('/names.html')
        assert_html_ok(resp)


class TestStats:
    def test_stats_page(self, client):
        resp = client.get('/stats.html')
        assert_html_ok(resp)


class TestYears:
    def test_years_page(self, client):
        resp = client.get('/years.html')
        assert_html_ok(resp)


# ── Features ─────────────────────────────────────────────────────────

class TestFeatures:
    def test_features_redirect(self, client):
        """No params → redirect to first feature."""
        resp = client.get('/features.html')
        assert resp.status_code in (301, 302, 308)

    def test_features_char1(self, client):
        resp = client.get('/features.html?f1=char1&f2=')
        assert_html_ok(resp)

    def test_features_last_char(self, client):
        resp = client.get('/features.html?f1=char_1&f2=')
        assert_html_ok(resp)

    def test_features_two_features(self, client):
        resp = client.get('/features.html?f1=char_2&f2=char_1')
        assert_html_ok(resp)


# ── Phenomena pages ──────────────────────────────────────────────────

class TestRedup:
    def test_redup_page(self, client):
        resp = client.get('/phenomena/redup.html')
        assert_html_ok(resp)


class TestJinmei:
    def test_jinmei_page(self, client):
        resp = client.get('/phenomena/jinmeiyou.html')
        assert_html_ok(resp)


class TestProportion:
    def test_proportion_page(self, client):
        resp = client.get('/phenomena/proportion.html')
        assert_html_ok(resp)


class TestIrregular:
    def test_irregular_page(self, client):
        resp = client.get('/irregular.html')
        assert_html_ok(resp)


class TestGenderedness:
    def test_genderedness_page(self, client):
        resp = client.get('/genderedness.html')
        assert_html_ok(resp)


class TestDiversity:
    def test_diversity_page(self, client):
        resp = client.get('/phenomena/diversity.html')
        assert_html_ok(resp, must_contain=['diversity', 'Diversity'])


class TestOverlap:
    def test_overlap_page(self, client):
        resp = client.get('/overlap.html')
        assert_html_ok(resp, must_contain=['Overlap'])

    def test_overlap_has_datasets(self, client):
        resp = client.get('/overlap.html')
        html = resp.data.decode()
        # Should have multiple source sections (now rendered as SVG + tables)
        assert 'overlap_bc_orth' in html


class TestAndrogyny:
    def test_androgyny_page(self, client):
        resp = client.get('/phenomena/androgyny.html')
        assert_html_ok(resp, must_contain=['Androgyn'])

    def test_androgyny_has_datasets(self, client):
        resp = client.get('/phenomena/androgyny.html')
        html = resp.data.decode()
        # Multiple source sections rendered as SVG + tables
        assert 'androgyny_bc' in html
        assert 'androgyny_hs' in html


class TestTopNames:
    def test_topnames_page(self, client):
        resp = client.get('/phenomena/topnames.html')
        assert_html_ok(resp, must_contain=['Top Names'])

    def test_topnames_has_all_sources(self, client):
        resp = client.get('/phenomena/topnames.html')
        html = resp.data.decode()
        assert 'const datasets' in html
        data = _extract_datasets(html)
        keys = [d['key'] for d in data]
        assert 'topnames_bc_orth' in keys
        assert 'topnames_bc_pron' in keys
        assert 'topnames_hs_orth' in keys
        assert 'topnames_meiji_orth' in keys
        assert 'topnames_meiji_pron' in keys

    def test_topnames_has_both_genders(self, client):
        resp = client.get('/phenomena/topnames.html')
        data = _extract_datasets(resp.data.decode())
        for ds in data:
            assert 'male' in ds, f"Missing male data in {ds['key']}"
            assert 'female' in ds, f"Missing female data in {ds['key']}"
            assert len(ds['male']['years']) > 0, f"No male years in {ds['key']}"
            assert len(ds['female']['years']) > 0, f"No female years in {ds['key']}"

    def test_topnames_has_top50_variant(self, client):
        resp = client.get('/phenomena/topnames.html')
        data = _extract_datasets(resp.data.decode())
        for ds in data:
            assert 'male_50' in ds, f"Missing male_50 in {ds['key']}"
            assert 'female_50' in ds, f"Missing female_50 in {ds['key']}"

    def test_topnames_ties_at_boundary(self, client):
        """Top 10 may include >10 entries when ties exist at rank 10."""
        resp = client.get('/phenomena/topnames.html')
        data = _extract_datasets(resp.data.decode())
        meiji_orth = [d for d in data if d['key'] == 'topnames_meiji_orth'][0]
        # Check any year — entries may exceed 10 due to ties
        nby = meiji_orth['male']['names_by_year']
        some_year = list(nby.keys())[-1]  # most recent year
        entries = nby[some_year]
        # All entries should have rank <= 10
        for e in entries:
            assert e['rank'] <= 10

    def test_topnames_number_ones_populated(self, client):
        resp = client.get('/phenomena/topnames.html')
        data = _extract_datasets(resp.data.decode())
        bc_orth = [d for d in data if d['key'] == 'topnames_bc_orth'][0]
        assert len(bc_orth['male']['number_ones']) > 0
        assert len(bc_orth['female']['number_ones']) > 0


# ── File download ────────────────────────────────────────────────────

class TestDownload:
    def test_download_valid_tsv(self, client):
        resp = client.get('/download/baby_calendar_names.tsv')
        assert resp.status_code == 200
        assert 'text/tab-separated-values' in resp.content_type or \
               'application/octet-stream' in resp.content_type

    def test_download_nonexistent(self, client):
        resp = client.get('/download/nonexistent.tsv')
        assert resp.status_code == 404


# ── Navigation consistency ───────────────────────────────────────────

class TestNavigation:
    """Ensure phenomena nav tabs appear on all phenomena pages."""

    @pytest.mark.parametrize("url", [
        '/phenomena/jinmeiyou.html',
        '/phenomena/redup.html',
        '/phenomena/diversity.html',
        '/overlap.html',
        '/phenomena/androgyny.html',
        '/phenomena/topnames.html',
    ])
    def test_phenomena_nav_tabs(self, client, url):
        resp = client.get(url)
        html = resp.data.decode()
        assert 'Top Names' in html, f"Top Names tab missing on {url}"
        assert 'Diversity' in html, f"Diversity tab missing on {url}"


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_datasets(html):
    """Extract the datasets JSON array from page HTML."""
    import re
    m = re.search(r'const datasets = (\[.*?\]);\s*$', html,
                  re.MULTILINE | re.DOTALL)
    assert m, "Could not find datasets JSON in page"
    return json.loads(m.group(1))


# ============================================================================
# Comprehensive per-model tests
# ============================================================================

# ---------------------------------------------------------------------------
# All static / universal pages load for every model
# ---------------------------------------------------------------------------

_UNIVERSAL_PAGES = [
    '/',
    '/phenomena/diversity.html',
    '/phenomena/androgyny.html',
    '/overlap.html',
    '/phenomena/topnames.html',
    '/genderedness.html',
    '/phenomena/jinmeiyou.html',
    '/phenomena/redup.html',
    '/phenomena/proportion.html',
]

_MODEL_PAGES = [
    '/names.html',
    '/stats.html',
    '/years.html',
]


@pytest.mark.slow
@pytest.mark.parametrize("db", list(db_options.keys()))
@pytest.mark.parametrize("url", _UNIVERSAL_PAGES)
def test_universal_page_all_models(app, db, url):
    """Every universal page must return 200 for every model."""
    client = app.test_client()
    _switch_db(client, db)
    resp = client.get(url)
    assert resp.status_code == 200, f"{url} [{db}] → {resp.status_code}"


@pytest.mark.slow
@pytest.mark.parametrize("db", list(db_options.keys()))
@pytest.mark.parametrize("url", _MODEL_PAGES)
def test_model_page_all_dbs(app, db, url):
    """Model-dependent pages must return 200 for every model."""
    client = app.test_client()
    _switch_db(client, db)
    resp = client.get(url)
    assert resp.status_code == 200, f"{url} [{db}] → {resp.status_code}"


# ---------------------------------------------------------------------------
# Name search — all four models × all search types
# ---------------------------------------------------------------------------

class TestNameSearchAllModels:
    """Search correctness and graceful-failure for every model/search combination."""

    @pytest.fixture(autouse=True)
    def fresh(self, app):
        self.client = app.test_client()

    def _get(self, url):
        return self.client.get(url)

    # Orth-supporting models
    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items() if caps['orth']])
    def test_orth_search(self, db):
        """Orth search works on all orth-supporting models."""
        _switch_db(self.client, db)
        resp = self._get(f'/namae?orth={SAMPLE_ORTH}')
        assert resp.status_code == 200
        assert SAMPLE_ORTH.encode() in resp.data

    # Pron-supporting models
    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items() if caps['pron']])
    def test_pron_search(self, db):
        """Pron search works on all pron-supporting models."""
        _switch_db(self.client, db)
        resp = self._get(f'/namae?pron={SAMPLE_PRON}')
        assert resp.status_code == 200

    # bc only: combined orth+pron search (愛/あい verified to exist in bc)
    def test_orth_and_pron_search_bc(self):
        """Combined orth+pron search works on bc."""
        _switch_db(self.client, 'bc')
        resp = self._get('/namae?orth=%E6%84%9B&pron=%E3%81%82%E3%81%84')  # 愛/あい
        assert resp.status_code == 200
        assert '愛'.encode() in resp.data

    # Graceful failures: pron search on orth-only models
    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items()
                                    if caps['orth'] and not caps['pron']])
    def test_pron_search_on_orth_only_model_graceful(self, db):
        """Pron search on orth-only model returns 200 with helpful error, not 500."""
        _switch_db(self.client, db)
        resp = self._get(f'/namae?pron={SAMPLE_PRON}')
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'not available' in html.lower() or 'error' in html.lower() or 'alert' in html.lower()

    # Graceful failures: orth search on pron-only model
    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items()
                                    if caps['pron'] and not caps['orth']])
    def test_orth_search_on_pron_only_model_graceful(self, db):
        """Orth search on pron-only model returns 200 with helpful error, not 500."""
        _switch_db(self.client, db)
        resp = self._get(f'/namae?orth={SAMPLE_ORTH}')
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'not available' in html.lower() or 'error' in html.lower() or 'alert' in html.lower()


# ---------------------------------------------------------------------------
# Kanji search — all models
# ---------------------------------------------------------------------------

class TestKanjiSearchAllModels:
    """Kanji search works for orth-supporting models; graceful for pron-only."""

    @pytest.fixture(autouse=True)
    def fresh(self, app):
        self.client = app.test_client()

    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items() if caps['kanji']])
    def test_kanji_search_supported(self, db):
        """Kanji lookup returns 200 and contains the kanji on supported models."""
        _switch_db(self.client, db)
        resp = self.client.get(f'/kanji?kanji={SAMPLE_KANJI}')
        assert resp.status_code == 200
        assert SAMPLE_KANJI.encode() in resp.data

    @pytest.mark.parametrize("db", [db for db, caps in DB_CAPS.items() if not caps['kanji']])
    def test_kanji_search_unsupported_graceful(self, db):
        """Kanji lookup on pron-only model returns 200 without crashing."""
        _switch_db(self.client, db)
        resp = self.client.get(f'/kanji?kanji={SAMPLE_KANJI}')
        assert resp.status_code == 200

    def test_single_quote_injection(self):
        """Single-quote in kanji param must not cause a 500."""
        _switch_db(self.client, 'bc')
        resp = self.client.get("/kanji?kanji='")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# All features × compatible databases
# ---------------------------------------------------------------------------

def _all_feature_params():
    params = []
    for f1, f2, name, possible in features:
        for db in possible:
            params.append(pytest.param(db, f1, f2, id=f"{db}/{name}"))
    return params


def _all_overall_params():
    params = []
    for f1, f2, name, possible in overall:
        for db in possible:
            params.append(pytest.param(db, f1, f2, id=f"{db}/{name}"))
    return params


@pytest.mark.slow
@pytest.mark.parametrize("db,f1,f2", _all_feature_params())
def test_feature_all_combos(app, db, f1, f2):
    """Every feature × compatible DB must return 200."""
    client = app.test_client()
    _switch_db(client, db)
    resp = client.get(f'/features.html?f1={f1}&f2={f2}&nm=test')
    assert resp.status_code == 200, f"features f1={f1} f2={f2} [{db}] → {resp.status_code}"


@pytest.mark.slow
@pytest.mark.parametrize("db,f1,f2", _all_overall_params())
def test_overall_all_combos(app, db, f1, f2):
    """Every overall feature × compatible DB must return 200."""
    client = app.test_client()
    _switch_db(client, db)
    resp = client.get(f'/features.html?f1={f1}&f2={f2}&nm=test')
    assert resp.status_code == 200, f"overall f1={f1} f2={f2} [{db}] → {resp.status_code}"


# ---------------------------------------------------------------------------
# Irregular page — bc only (only source with orth+pron)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("db", list(db_options.keys()))
def test_irregular_all_models(app, db):
    """Irregular page must return 200 for every model (always uses bc data)."""
    client = app.test_client()
    _switch_db(client, db)
    resp = client.get('/irregular.html')
    assert resp.status_code == 200, f"/irregular.html [{db}] → {resp.status_code}"
