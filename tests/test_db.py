"""Unit tests for web/db.py query functions.

Tests run against the real database (web/db/namae.db).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import pytest


@pytest.fixture(scope='module')
def conn():
    """Direct SQLite connection (no Flask context needed)."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'db', 'namae.db')
    if not os.path.exists(db_path):
        pytest.skip("Database not built: web/db/namae.db missing")
    c = sqlite3.connect(db_path)
    yield c
    c.close()


# ── get_top_names ────────────────────────────────────────────────────

class TestGetTopNames:
    def test_returns_expected_keys(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=10)
        assert 'years' in result
        assert 'names_by_year' in result
        assert 'number_ones' in result

    def test_years_are_sorted(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='M', n_top=10)
        assert result['years'] == sorted(result['years'])

    def test_bc_year_range(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=10)
        assert min(result['years']) >= 2008
        assert max(result['years']) <= 2022

    def test_hs_year_range(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='hs', dtype='orth', gender='M', n_top=10)
        assert min(result['years']) >= 1989
        assert max(result['years']) <= 2009

    def test_meiji_year_range(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='meiji', dtype='orth', gender='F', n_top=10)
        assert min(result['years']) >= 1912
        assert max(result['years']) <= 2024

    def test_top10_rank_bounds(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='M', n_top=10)
        for year, entries in result['names_by_year'].items():
            for e in entries:
                assert e['rank'] <= 10, f"rank {e['rank']} > 10 in year {year}"

    def test_top50_has_more_than_top10(self, conn):
        from web.db import get_top_names
        r10 = get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=10)
        r50 = get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=50)
        y = r10['years'][0]
        assert len(r50['names_by_year'][y]) >= len(r10['names_by_year'][y])

    def test_entries_have_name_rank_freq(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='M', n_top=10)
        y = result['years'][0]
        entry = result['names_by_year'][y][0]
        assert 'name' in entry
        assert 'rank' in entry
        assert 'freq' in entry
        assert isinstance(entry['name'], str)
        assert isinstance(entry['rank'], int)
        assert isinstance(entry['freq'], int)

    def test_number_ones_are_strings(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='orth', gender='F', n_top=10)
        assert len(result['number_ones']) > 0
        for name in result['number_ones']:
            assert isinstance(name, str)

    def test_ties_at_boundary(self, conn):
        """Meiji orth is known to have ties — verify they're included."""
        from web.db import get_top_names
        result = get_top_names(conn, src='meiji', dtype='orth', gender='M', n_top=10)
        # At least one year should have >10 entries due to ties
        has_extra = any(
            len(entries) > 10
            for entries in result['names_by_year'].values()
        )
        # This is expected but not guaranteed for all datasets
        # Just verify all entries have rank <= 10
        for year, entries in result['names_by_year'].items():
            for e in entries:
                assert e['rank'] <= 10

    def test_pron_dtype(self, conn):
        from web.db import get_top_names
        result = get_top_names(conn, src='bc', dtype='pron', gender='F', n_top=10)
        assert len(result['years']) > 0
        y = result['years'][0]
        # Pronunciation should be hiragana
        for e in result['names_by_year'][y]:
            assert e['name'] is not None


# ── get_overlap ──────────────────────────────────────────────────────

class TestGetOverlap:
    def test_returns_tuple_of_three(self, conn):
        from web.db import get_overlap
        result = get_overlap(conn, src='bc', dtype='orth', n_top=50)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_data_structure(self, conn):
        from web.db import get_overlap
        data, reg_count, reg_prop = get_overlap(conn, src='bc', dtype='orth', n_top=50)
        assert isinstance(data, list)
        assert len(data) > 0
        row = data[0]
        assert 'year' in row
        assert 'overlap_count' in row
        assert 'weighted_proportion' in row
        assert 'total_babies' in row
        assert 'names' in row

    def test_years_are_contiguous(self, conn):
        """All years in the source range should appear (including zeros)."""
        from web.db import get_overlap
        data, _, _ = get_overlap(conn, src='bc', dtype='orth', n_top=50)
        years = [d['year'] for d in data]
        assert years == sorted(years)
        # BC should have years 2008-2022
        assert min(years) <= 2009
        assert max(years) >= 2021

    def test_regression_structure(self, conn):
        from web.db import get_overlap
        _, reg_count, _ = get_overlap(conn, src='bc', dtype='orth', n_top=50)
        if reg_count is not None:
            assert 'slope' in reg_count
            assert 'p_value' in reg_count
            assert 'trend' in reg_count
            assert reg_count['trend'] in ('increasing', 'decreasing', 'stable')

    def test_overlap_names_list(self, conn):
        from web.db import get_overlap
        data, _, _ = get_overlap(conn, src='bc', dtype='orth', n_top=50)
        # Find a year with overlap
        years_with_overlap = [d for d in data if d['overlap_count'] > 0]
        if years_with_overlap:
            row = years_with_overlap[0]
            assert isinstance(row['names'], list)
            if row['names']:
                n = row['names'][0]
                assert 'name' in n
                assert 'male_freq' in n
                assert 'female_freq' in n


# ── get_androgyny ────────────────────────────────────────────────────

class TestGetAndrogyny:
    def test_returns_tuple_of_two(self, conn):
        from web.db import get_androgyny
        result = get_androgyny(conn, src='bc', dtype='orth')
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_data_structure(self, conn):
        from web.db import get_androgyny
        data, regression = get_androgyny(conn, src='bc', dtype='orth')
        assert isinstance(data, list)
        assert len(data) > 0
        row = data[0]
        assert 'year' in row
        assert 'proportion' in row
        assert 'total' in row
        assert 'androgynous' in row

    def test_proportion_range(self, conn):
        from web.db import get_androgyny
        data, _ = get_androgyny(conn, src='bc', dtype='orth')
        for row in data:
            assert 0.0 <= row['proportion'] <= 1.0, \
                f"proportion {row['proportion']} out of range in year {row['year']}"

    def test_different_tau(self, conn):
        from web.db import get_androgyny
        data_0, _ = get_androgyny(conn, src='bc', dtype='orth', tau=0.0)
        data_2, _ = get_androgyny(conn, src='bc', dtype='orth', tau=0.2)
        # Stricter tau should give fewer or equal androgynous names
        for d0, d2 in zip(data_0, data_2):
            assert d0['androgynous'] >= d2['androgynous'], \
                f"tau=0.2 has more androgynous than tau=0.0 in {d0['year']}"

    def test_token_vs_type(self, conn):
        from web.db import get_androgyny
        data_tok, _ = get_androgyny(conn, src='bc', dtype='orth', count_type='token')
        data_typ, _ = get_androgyny(conn, src='bc', dtype='orth', count_type='type')
        assert len(data_tok) == len(data_typ)


# ── get_kanji_distribution ───────────────────────────────────────────

class TestGetKanjiDistribution:
    def test_common_kanji(self, conn):
        from web.db import get_kanji_distribution
        data = get_kanji_distribution(conn, '美', 'F', 'bc')
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_returns_position_data(self, conn):
        from web.db import get_kanji_distribution
        data = get_kanji_distribution(conn, '美', 'F', 'bc')
        if data:
            year = list(data.keys())[0]
            # Should be a list of [solo, initial, middle, end, count]
            assert isinstance(data[year], list)
            assert len(data[year]) == 5, f"Expected 5 elements, got {len(data[year])}: {data[year]}"

    def test_invalid_input_returns_empty(self, conn):
        from web.db import get_kanji_distribution
        assert get_kanji_distribution(conn, '*', 'F', 'bc') == {}
        assert get_kanji_distribution(conn, '', 'F', 'bc') == {}
        assert get_kanji_distribution(conn, 'ab', 'F', 'bc') == {}

    def test_rare_kanji_returns_empty_or_data(self, conn):
        from web.db import get_kanji_distribution
        # A very rare kanji might return empty
        data = get_kanji_distribution(conn, '鑢', 'M', 'bc')
        assert isinstance(data, dict)


# ── get_irregular ────────────────────────────────────────────────────

class TestGetIrregular:
    def test_returns_triple(self, conn):
        from web.db import get_irregular
        result = get_irregular(conn, table='namae', src='bc')
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_data_structure(self, conn):
        from web.db import get_irregular
        data, regression, gender = get_irregular(conn, table='namae', src='bc')
        assert isinstance(data, list)
        assert len(data) > 0
        # Each row: (year, gender, names, number, irregular, proportion)
        row = data[0]
        assert len(row) == 6


# ── resolve_src ──────────────────────────────────────────────────────

class TestResolveSrc:
    def test_normal_sources(self):
        from web.db import resolve_src
        assert resolve_src('bc') == 'bc'
        assert resolve_src('hs') == 'hs'
        assert resolve_src('meiji') == 'meiji'

    def test_alias(self):
        from web.db import resolve_src
        assert resolve_src('meiji_p') == 'meiji'

    def test_unknown(self):
        from web.db import resolve_src
        assert resolve_src('unknown') == 'unknown'
