"""Data integrity sanity checks against the built database.

These tests verify known facts about the data, catching build pipeline
regressions (e.g. missing sources, wrong year ranges, broken aggregations).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import pytest


@pytest.fixture(scope='module')
def conn():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'db', 'namae.db')
    if not os.path.exists(db_path):
        pytest.skip("Database not built: web/db/namae.db missing")
    c = sqlite3.connect(db_path)
    yield c
    c.close()


# ── Table existence ──────────────────────────────────────────────────

class TestSchema:
    @pytest.mark.parametrize("table", [
        'namae', 'nrank', 'name_year_cache', 'attr', 'kanji', 'ntok',
    ])
    def test_table_exists(self, conn, table):
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,))
        assert cur.fetchone() is not None, f"Table {table} missing"

    def test_combined_view_exists(self, conn):
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' AND name='combined'")
        assert cur.fetchone() is not None


# ── Source coverage ──────────────────────────────────────────────────

class TestSourceCoverage:
    def test_namae_sources(self, conn):
        cur = conn.execute("SELECT DISTINCT src FROM namae ORDER BY src")
        sources = {r[0] for r in cur}
        assert 'bc' in sources
        assert 'hs' in sources
        assert 'meiji' in sources

    def test_nrank_sources(self, conn):
        cur = conn.execute("SELECT DISTINCT src FROM nrank ORDER BY src")
        sources = {r[0] for r in cur}
        assert 'bc' in sources
        assert 'hs' in sources
        assert 'meiji' in sources

    def test_cache_sources(self, conn):
        cur = conn.execute("SELECT DISTINCT src FROM name_year_cache ORDER BY src")
        sources = {r[0] for r in cur}
        assert 'bc' in sources
        assert 'hs' in sources
        assert 'meiji' in sources
        assert 'births' in sources


# ── Year ranges ──────────────────────────────────────────────────────

class TestYearRanges:
    def test_bc_years(self, conn):
        cur = conn.execute(
            "SELECT MIN(year), MAX(year) FROM namae WHERE src='bc'")
        mn, mx = cur.fetchone()
        assert mn == 2008
        assert mx == 2022

    def test_hs_years(self, conn):
        cur = conn.execute(
            "SELECT MIN(year), MAX(year) FROM namae WHERE src='hs'")
        mn, mx = cur.fetchone()
        assert mn == 1989
        assert mx == 2009

    def test_meiji_nrank_years(self, conn):
        cur = conn.execute(
            "SELECT MIN(year), MAX(year) FROM nrank WHERE src='meiji'")
        mn, mx = cur.fetchone()
        assert mn <= 1912
        assert mx >= 2024

    def test_births_years(self, conn):
        cur = conn.execute(
            "SELECT MIN(year), MAX(year) FROM name_year_cache WHERE src='births'")
        mn, mx = cur.fetchone()
        assert mn <= 1900
        assert mx >= 2022


# ── Row count sanity ─────────────────────────────────────────────────

class TestRowCounts:
    def test_namae_not_empty(self, conn):
        cur = conn.execute("SELECT COUNT(*) FROM namae")
        assert cur.fetchone()[0] > 100000

    def test_nrank_not_empty(self, conn):
        cur = conn.execute("SELECT COUNT(*) FROM nrank")
        assert cur.fetchone()[0] > 1000

    def test_kanji_populated(self, conn):
        cur = conn.execute("SELECT COUNT(*) FROM kanji")
        assert cur.fetchone()[0] > 500

    def test_attr_covers_namae(self, conn):
        """attr should have roughly as many rows as namae."""
        namae_ct = conn.execute("SELECT COUNT(*) FROM namae").fetchone()[0]
        attr_ct = conn.execute("SELECT COUNT(*) FROM attr").fetchone()[0]
        # Allow some slack — attr may skip rows with NULL orth
        assert attr_ct >= namae_ct * 0.9


# ── Gender values ────────────────────────────────────────────────────

class TestGenderValues:
    def test_namae_genders(self, conn):
        cur = conn.execute("SELECT DISTINCT gender FROM namae ORDER BY gender")
        genders = {r[0] for r in cur}
        assert genders == {'F', 'M'}

    def test_nrank_genders(self, conn):
        cur = conn.execute("SELECT DISTINCT gender FROM nrank ORDER BY gender")
        genders = {r[0] for r in cur}
        assert genders == {'F', 'M'}


# ── Known name spot checks ──────────────────────────────────────────

class TestKnownNames:
    def test_taro_exists_in_hs(self, conn):
        """太郎 should appear in Heisei."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM namae WHERE src='hs' AND orth='太郎'")
        assert cur.fetchone()[0] > 0

    def test_hanako_exists(self, conn):
        """花子 should appear in at least one source."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM namae WHERE orth='花子'")
        assert cur.fetchone()[0] > 0

    def test_bc_has_pron(self, conn):
        """Baby Calendar should have pronunciation data."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM namae WHERE src='bc' AND pron IS NOT NULL")
        assert cur.fetchone()[0] > 10000

    def test_hs_no_pron(self, conn):
        """Heisei should NOT have pronunciation data."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM namae WHERE src='hs' AND pron IS NOT NULL")
        assert cur.fetchone()[0] == 0

    def test_meiji_has_null_orth_in_nrank(self, conn):
        """Meiji pron-only entries have orth IS NULL in nrank."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE src='meiji' AND orth IS NULL AND pron IS NOT NULL")
        assert cur.fetchone()[0] > 0

    def test_meiji_has_null_pron_in_nrank(self, conn):
        """Meiji orth-only entries have pron IS NULL in nrank."""
        cur = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE src='meiji' AND pron IS NULL AND orth IS NOT NULL")
        assert cur.fetchone()[0] > 0


# ── nrank consistency ────────────────────────────────────────────────

class TestNrankConsistency:
    def test_bc_nrank_ranks_start_at_1(self, conn):
        cur = conn.execute(
            "SELECT MIN(rank) FROM nrank WHERE src='bc'")
        assert cur.fetchone()[0] == 1

    def test_freqs_are_positive(self, conn):
        cur = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE freq <= 0")
        assert cur.fetchone()[0] == 0

    def test_ranks_are_positive(self, conn):
        cur = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE rank <= 0")
        assert cur.fetchone()[0] == 0

    def test_bc_has_orth_and_pron_rankings(self, conn):
        """BC nrank has both orth-only and pron-only rows."""
        orth_only = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE src='bc' AND orth IS NOT NULL AND pron IS NULL"
        ).fetchone()[0]
        pron_only = conn.execute(
            "SELECT COUNT(*) FROM nrank WHERE src='bc' AND pron IS NOT NULL AND orth IS NULL"
        ).fetchone()[0]
        assert orth_only > 0
        assert pron_only > 0
