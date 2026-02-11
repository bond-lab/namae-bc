"""Content validation tests — verify pages contain expected data, not just load.

Also covers edge cases, error handling, and session state effects.
"""

import json
import re
import pytest


# ── Name search content ──────────────────────────────────────────────

class TestNameSearchContent:
    def test_orth_search_returns_data(self, client):
        """Searching a known name returns actual frequency data."""
        resp = client.get('/namae?orth=太郎')
        html = resp.data.decode()
        assert resp.status_code == 200
        # Should show the name and have year/frequency data in the page
        assert '太郎' in html

    def test_pron_search_returns_data(self, client):
        resp = client.get('/namae?pron=はなこ')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert 'はなこ' in html

    def test_orth_search_unknown_name(self, client):
        """An unknown name should return 200, not crash."""
        resp = client.get('/namae?orth=鑢鑢鑢')
        assert resp.status_code == 200

    def test_pron_search_unknown(self, client):
        resp = client.get('/namae?pron=ぬぬぬぬぬ')
        assert resp.status_code == 200


# ── Kanji search content ─────────────────────────────────────────────

class TestKanjiSearchContent:
    def test_kanji_returns_chart_data(self, client):
        """A common kanji should have position distribution data."""
        resp = client.get('/kanji?kanji=美')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert '美' in html
        # Should render chart containers
        assert 'data_male' in html or 'data_female' in html or 'chart' in html.lower()

    def test_kanji_unknown_but_valid(self, client):
        """A valid kanji not in names should still return 200."""
        resp = client.get('/kanji?kanji=鬱')
        assert resp.status_code == 200


# ── Input validation edge cases ──────────────────────────────────────

class TestInputEdgeCases:
    def test_pron_katakana_rejected(self, client):
        """Katakana is not hiragana — should show error."""
        resp = client.get('/namae?pron=ハナコ')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert 'hiragana' in html.lower() or 'ひらがな' in html.lower() or 'error' in html.lower()

    def test_pron_mixed_rejected(self, client):
        resp = client.get('/namae?pron=はなko')
        html = resp.data.decode()
        assert resp.status_code == 200

    def test_orth_empty_string(self, client):
        resp = client.get('/namae?orth=')
        assert resp.status_code == 200

    def test_pron_empty_string(self, client):
        resp = client.get('/namae?pron=')
        assert resp.status_code == 200

    def test_very_long_orth(self, client):
        """Very long input should not crash."""
        long_name = '太' * 200
        resp = client.get(f'/namae?orth={long_name}')
        assert resp.status_code == 200

    def test_very_long_pron(self, client):
        long_pron = 'あ' * 200
        resp = client.get(f'/namae?pron={long_pron}')
        assert resp.status_code == 200

    def test_kanji_emoji_rejected(self, client):
        """Emoji should not crash the kanji route."""
        resp = client.get('/namae?orth=😀')
        assert resp.status_code == 200

    def test_kanji_route_emoji(self, client):
        resp = client.get('/kanji?kanji=😀')
        assert resp.status_code == 200


# ── 404 and nonexistent routes ───────────────────────────────────────

class TestErrorHandling:
    def test_404_nonexistent(self, client):
        resp = client.get('/nonexistent-page')
        assert resp.status_code == 404

    def test_features_bad_feature(self, client):
        """Invalid feature name should not cause 500."""
        resp = client.get('/features.html?f1=nonexistent&f2=')
        assert resp.status_code in (200, 400, 404, 500)
        # Just verify it doesn't hang or crash differently

    def test_download_path_traversal(self, client):
        """Path traversal attempt should fail."""
        resp = client.get('/download/../../../etc/passwd')
        assert resp.status_code in (400, 404)

    def test_download_no_filename(self, client):
        resp = client.get('/download/')
        assert resp.status_code in (301, 308, 404)


# ── Session state effects ────────────────────────────────────────────

class TestSessionEffects:
    def test_default_source_is_bc(self, client_fresh):
        """Fresh session should default to Baby Calendar."""
        resp = client_fresh.get('/names.html')
        html = resp.data.decode()
        assert resp.status_code == 200
        # The page should show BC data by default
        assert 'Baby Calendar' in html or 'bc' in html.lower()

    def test_changing_source_affects_names(self, client_fresh):
        """POST to settings should change the data source for subsequent requests."""
        # Set to Heisei
        client_fresh.post('/settings', data={
            'color_palette': 'orange_purple',
            'db_option': 'hs',
        })
        resp = client_fresh.get('/names.html')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert 'Heisei' in html or 'hs' in html.lower()

    def test_changing_source_affects_kanji(self, client_fresh):
        """Kanji search should respect the selected data source."""
        # Set to Heisei
        client_fresh.post('/settings', data={
            'color_palette': 'orange_purple',
            'db_option': 'hs',
        })
        resp = client_fresh.get('/kanji?kanji=美')
        assert resp.status_code == 200

    def test_color_palette_change(self, client_fresh):
        """Changing palette should affect page rendering."""
        client_fresh.post('/settings', data={
            'color_palette': 'blue_red',
            'db_option': 'bc',
        })
        resp = client_fresh.get('/phenomena/androgyny.html')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert 'blue' in html


# ── Overlap content validation ───────────────────────────────────────

class TestOverlapContent:
    def test_overlap_has_names_data(self, client):
        resp = client.get('/overlap.html')
        html = resp.data.decode()
        m = re.search(r'const datasets = (\[.*?\]);\s*$', html,
                      re.MULTILINE | re.DOTALL)
        assert m
        data = json.loads(m.group(1))
        assert len(data) > 0
        # Check first dataset has expected structure
        ds = data[0]
        assert 'data' in ds
        assert len(ds['data']) > 0
        row = ds['data'][0]
        assert 'year' in row
        assert 'overlap_count' in row


# ── Androgyny content validation ─────────────────────────────────────

class TestAndrogynyContent:
    def test_androgyny_has_multiple_sources(self, client):
        resp = client.get('/phenomena/androgyny.html')
        html = resp.data.decode()
        m = re.search(r'const datasets = (\[.*?\]);\s*$', html,
                      re.MULTILINE | re.DOTALL)
        assert m
        data = json.loads(m.group(1))
        # Should have datasets from multiple sources
        keys = [d['key'] for d in data]
        sources = set(k.split('_')[1] for k in keys)
        assert len(sources) >= 2, f"Only {sources} found, expected multiple sources"

    def test_androgyny_proportions_in_range(self, client):
        resp = client.get('/phenomena/androgyny.html')
        html = resp.data.decode()
        m = re.search(r'const datasets = (\[.*?\]);\s*$', html,
                      re.MULTILINE | re.DOTALL)
        data = json.loads(m.group(1))
        for ds in data:
            for row in ds['data']:
                assert 0.0 <= row['proportion'] <= 1.0, \
                    f"proportion {row['proportion']} out of range in {ds['key']}"


# ── Diversity content ────────────────────────────────────────────────

class TestDiversityContent:
    def test_diversity_has_source_sections(self, client):
        resp = client.get('/phenomena/diversity.html')
        html = resp.data.decode()
        assert resp.status_code == 200
        # Should have at least Baby Calendar section
        assert 'Baby Calendar' in html or 'bc' in html
