"""Regression tests for all web routes.

Run with:  pytest tests/ -v
Requires:  web/db/namae.db (built via makedb.sh)
"""

import json
import pytest


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
    @pytest.mark.xfail(reason="Template phenomena/proportion.html does not exist yet")
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
        assert 'const datasets' in html
        # Should have multiple source cards
        assert 'overlap_bc_orth' in html


class TestAndrogyny:
    def test_androgyny_page(self, client):
        resp = client.get('/phenomena/androgyny.html')
        assert_html_ok(resp, must_contain=['Androgyn'])

    def test_androgyny_has_datasets(self, client):
        resp = client.get('/phenomena/androgyny.html')
        html = resp.data.decode()
        assert 'const datasets' in html


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
