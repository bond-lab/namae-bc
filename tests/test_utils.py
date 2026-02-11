"""Unit tests for web/utils.py — mora, syllable, script detection."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from web.utils import mora_hiragana, syllable_hiragana, whichScript, expand_r


# ── whichScript ──────────────────────────────────────────────────────

class TestWhichScript:
    def test_pure_katakana(self):
        assert whichScript('カタカナ') == 'kata'

    def test_katakana_with_prolonged(self):
        assert whichScript('カタ・カナー') == 'kata'

    def test_pure_hiragana(self):
        assert whichScript('こんにちは') == 'hira'

    def test_pure_kanji(self):
        assert whichScript('耀士郎') == 'kanji'

    def test_kanji_hiragana_mix(self):
        assert whichScript('くる美') == 'mixhira'

    def test_kanji_katakana_mix(self):
        assert whichScript('カタ美') == 'mixkata'

    def test_kanji_with_katakana_particle(self):
        # ノ is katakana
        assert whichScript('隆ノ介') == 'mixkata'

    def test_single_kanji(self):
        assert whichScript('翔') == 'kanji'

    def test_single_hiragana(self):
        assert whichScript('あ') == 'hira'

    def test_single_katakana(self):
        assert whichScript('ア') == 'kata'


# ── mora_hiragana ────────────────────────────────────────────────────

class TestMoraHiragana:
    def test_empty(self):
        assert mora_hiragana('') == []

    def test_simple(self):
        assert mora_hiragana('こんにちは') == ['こ', 'ん', 'に', 'ち', 'は']

    def test_yoon(self):
        """Contracted sounds (拗音) merge into one mora."""
        assert mora_hiragana('とうきょう') == ['と', 'う', 'きょ', 'う']

    def test_yoon_at_start(self):
        assert mora_hiragana('しゃしん') == ['しゃ', 'し', 'ん']

    def test_multiple_yoon(self):
        assert mora_hiragana('うぇりゃむ') == ['うぇ', 'りゃ', 'む']

    def test_n_mora(self):
        assert mora_hiragana('あん') == ['あ', 'ん']

    def test_non_hiragana_raises(self):
        with pytest.raises(AssertionError, match="not Hiragana"):
            mora_hiragana('abc')

    def test_kanji_raises(self):
        with pytest.raises(AssertionError, match="not Hiragana"):
            mora_hiragana('太郎')

    def test_common_names(self):
        assert mora_hiragana('はなこ') == ['は', 'な', 'こ']
        assert mora_hiragana('たろう') == ['た', 'ろ', 'う']
        assert mora_hiragana('しょうた') == ['しょ', 'う', 'た']


# ── syllable_hiragana ────────────────────────────────────────────────

class TestSyllableHiragana:
    def test_empty(self):
        assert syllable_hiragana([]) == []

    def test_n_joins(self):
        """ん joins with preceding mora."""
        assert syllable_hiragana(['こ', 'ん', 'に', 'ち', 'は']) == \
            ['こん', 'に', 'ち', 'は']

    def test_vowel_joins(self):
        """Long vowels join with preceding mora."""
        assert syllable_hiragana(['と', 'う', 'きょ', 'う']) == \
            ['とう', 'きょう']

    def test_geminate(self):
        """っ joins with preceding mora."""
        assert syllable_hiragana(['き', 'っ', 'て']) == ['きっ', 'て']

    def test_single_vowel_syllable(self):
        assert syllable_hiragana(['じょ', 'う']) == ['じょう']

    def test_complex(self):
        assert syllable_hiragana(['うぇ', 'りゃ', 'む']) == \
            ['うぇ', 'りゃ', 'む']

    def test_n_after_vowel(self):
        assert syllable_hiragana(['あ', 'ん', 'い']) == ['あん', 'い']

    def test_trailing_n(self):
        assert syllable_hiragana(['あ', 'い', 'ん']) == ['あ', 'いん']

    def test_prolonged_mark(self):
        assert syllable_hiragana(['あ', 'い', 'み', 'ー']) == ['あい', 'みー']

    def test_not_list_raises(self):
        with pytest.raises(AssertionError, match="not a list"):
            syllable_hiragana('abc')


# ── expand_r ─────────────────────────────────────────────────────────

class TestExpandR:
    def test_dot_reading(self):
        assert expand_r(['ちい.さい']) == ['ちいさい', 'ちい', 'さい']

    def test_dash_reading(self):
        assert expand_r(['こ-']) == ['こ']

    def test_plain(self):
        assert expand_r(['あい']) == ['あい']

    def test_multiple(self):
        result = expand_r(['ちい.さい', 'こ-'])
        assert 'ちいさい' in result
        assert 'こ' in result
