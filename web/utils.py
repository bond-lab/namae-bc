import regex

_YOON = {"ゃ", "ゅ", "ょ", "ぁ", "ぃ", "ぇ", "ゎ"}    # Obsolete:  ゎ ぇ o, u

_OWARI = {"ん", "っ"}

_A_COLUMN = [
    'あ',  # A-gyou
    'か', 'が',  # K-gyou
    'さ', 'ざ',  # S-gyou
    'た', 'だ',  # T-gyou
    'な',  # N-gyou
    'は', 'ば', 'ぱ',  # H-gyou
    'ま',  # M-gyou
    'や',  # Y-gyou
    'ら',  # R-gyou
    'わ',  # W-gyou
    'きゃ', 'ぎゃ',  # K-gyou small vowel
    'しゃ', 'じゃ',  # S-gyou small vowel
    'ちゃ', 'ぢゃ',  # T-gyou small vowel
    'にゃ',  # N-gyou small vowel
    'ひゃ', 'びゃ', 'ぴゃ',  # H-gyou small vowel
    'みゃ',  # M-gyou small vowel
    'りゃ'   # R-gyou small vowel
]

_I_COLUMN = [
    'い',  # A-gyou
    'き', 'ぎ',  # K-gyou
    'し', 'じ',  # S-gyou
    'ち', 'ぢ',  # T-gyou
    'に',  # N-gyou
    'ひ', 'び', 'ぴ',  # H-gyou
    'み',  # M-gyou
    'り',  # R-gyou
    'きぃ', 'ぎぃ',  # K-gyou small vowel
    'しぃ', 'じぃ',  # S-gyou small vowel
    'ちぃ', 'ぢぃ',  # T-gyou small vowel
    'にぃ',  # N-gyou small vowel
    'ひぃ', 'びぃ', 'ぴぃ',  # H-gyou small vowel
    'みぃ',  # M-gyou small vowel
    'りぃ'   # R-gyou small vowel
]


_U_COLUMN = [
    'う',  # A-gyou
    'く', 'ぐ',  # K-gyou
    'す', 'ず',  # S-gyou
    'つ', 'づ',  # T-gyou
    'ぬ',  # N-gyou
    'ふ', 'ぶ', 'ぷ',  # H-gyou
    'む',  # M-gyou
    'ゆ',  # Y-gyou
    'る',  # R-gyou
    'きゅ', 'ぎゅ',  # K-gyou small vowel
    'しゅ', 'じゅ',  # S-gyou small vowel
    'ちゅ', 'ぢゅ',  # T-gyou small vowel
    'にゅ',  # N-gyou small vowel
    'ひゅ', 'びゅ', 'ぴゅ',  # H-gyou small vowel
    'みゅ',  # M-gyou small vowel
    'りゅ'   # R-gyou small vowel
]


_E_COLUMN = [
    'え',  # A-gyou
    'け', 'げ',  # K-gyou
    'せ', 'ぜ',  # S-gyou
    'て', 'で',  # T-gyou
    'ね',  # N-gyou
    'へ', 'べ', 'ぺ',  # H-gyou
    'め',  # M-gyou
    'れ',  # R-gyou
    'しぇ', 'じぇ',  # S-gyou small vowel
    'ちぇ', 'ぢぇ',  # T-gyou small vowel
    'にぇ',  # N-gyou small vowel
    'ひぇ', 'びぇ', 'ぴぇ',  # H-gyou small vowel
    'みぇ',  # M-gyou small vowel
    'りぇ'   # R-gyou small vowel
]



_O_COLUMN = [
    'お',  # A-gyou
    'こ', 'ご',  # K-gyou
    'そ', 'ぞ',  # S-gyou
    'と', 'ど',  # T-gyou
    'の',  # N-gyou
    'ほ', 'ぼ', 'ぽ',  # H-gyou
    'も',  # M-gyou
    'よ',  # Y-gyou
    'ろ',  # R-gyou
    'を',  # W-gyou
    'きょ', 'ぎょ',  # K-gyou small vowel
    'しょ', 'じょ',  # S-gyou small vowel
    'ちょ', 'ぢょ',  # T-gyou small vowel
    'にょ',  # N-gyou small vowel
    'ひょ', 'びょ', 'ぴょ',  # H-gyou small vowel
    'みょ',  # M-gyou small vowel
    'りょ'   # R-gyou small vowel
]

### the key can follow the values
_BOUIN = {"あ":_A_COLUMN,
          "い":_A_COLUMN + _I_COLUMN + _E_COLUMN,
          "う":_A_COLUMN + _U_COLUMN + _O_COLUMN,
          "え":_E_COLUMN, ### is moe a syllable?
          "お":_O_COLUMN,
          "ー": _A_COLUMN + _I_COLUMN + _U_COLUMN +  _E_COLUMN + _O_COLUMN
}



def whichScript (name):
    """
    is the entire name katakana
    >>> whichScript("カタ・カナー")
    'kata'
    >>> whichScript ("こんにちは")
    'hira'
    >>> whichScript ("くる美")
    'mixhira'
    >>> whichScript ("カタ美")
    'mixkata'
    >>> whichScript ("隆ノ介")
    'mixkata'
    >>> whichScript ("耀士郎")
    'kanji'
    """
    if regex.match(r'^[\p{scx=Katakana}]+$', name):
        return 'kata'
    elif regex.match(r'^[\p{scx=Hiragana}]+$', name):
        return 'hira'
    elif regex.search(r'[\p{scx=Hiragana}]', name): 
        return 'mixhira'
    elif regex.search(r'[\p{scx=Katakana}]', name):
        return 'mixkata'
    else:
        return 'kanji'

def mora_hiragana(word):
  """Splits a Japanese word in hiragana into mora.

  Args:
    word: The Japanese word in hiragana to split.

  Returns:
    A list of morae.

  Raises:
    ValueError: If an invalid character is encountered.

  Examples:
    >>> mora_hiragana('こんにちは')
    ['こ', 'ん', 'に', 'ち', 'は']
    >>> mora_hiragana('とうきょう')
    ['と', 'う', 'きょ', 'う']
    >>> mora_hiragana('うぇりゃむ')
    ['うぇ', 'りゃ', 'む']
    >>> mora_hiragana('あん')
    ['あ', 'ん']
    >>> mora_hiragana('')
    []
    >>> mora_hiragana('abc')
    Traceback (most recent call last):
       ...
    AssertionError: not Hiragana
  """
  if not word:
    return []
  else:
    assert regex.match(r'^[\p{scx=Hiragana}]+$', word), "not Hiragana"
  mora = []
  for char in word:
    if char in _YOON:
      if mora:
        mora[-1] += char
      else:
        "this should not happen"
    else:
      mora.append(char)

  return mora


    
def syllable_hiragana(mora):
  """
  Takes a list of syllable and joins syllables.

  Args:
    mora: A list of mora (in Hiragana)

  Returns:
    A list of syllables.

  Raises:
    ValueError: If the input is not a list

  Examples:
    >>> syllable_hiragana(['こ', 'ん', 'に', 'ち', 'は'])
    ['こん', 'に', 'ち', 'は']
    >>> syllable_hiragana(['と', 'う', 'きょ', 'う'])
    ['とう', 'きょう']
    >>> syllable_hiragana(['き', 'っ', 'て'])
    ['きっ', 'て']
    >>> syllable_hiragana(['じょ', 'う'])
    ['じょう']
    >>> syllable_hiragana(['うぇ', 'りゃ', 'む'])
    ['うぇ', 'りゃ', 'む']
    >>> syllable_hiragana(['あ', 'ん', 'い'])
    ['あん', 'い']
    >>> syllable_hiragana(['あ', 'い', 'ん'])
    ['あ', 'いん']
    >>> syllable_hiragana(['こ', 'あ', 'か', 'い'])
    ['こ', 'あ', 'かい']
    >>> syllable_hiragana(['し', 'お', 'う'])
    ['し', 'おう']
    >>> syllable_hiragana(['あ', 'お', 'い'])
    ['あ', 'お', 'い']
    >>> syllable_hiragana(['あ', 'い', 'み', 'ー'])
    ['あい', 'みー']
    >>> syllable_hiragana(['ろ', 'お', 'い'])
    ['ろお', 'い']
    >>> syllable_hiragana([])
    []
    >>> syllable_hiragana('abc')
    Traceback (most recent call last):
       ...
    AssertionError: not a list
  """
  assert isinstance(mora, list), "not a list"
  syllable = []
  i = 0
  while i < len(mora):
      m = mora[i]
      if i +1 < len(mora):
          n = mora[i+1]  ### next
      else:
          n = ''
      if n in _OWARI:
          syllable.append(m + n)
          i += 2
      elif n in _BOUIN and m in _BOUIN[n]:
          if i + 2 < len(mora):
              o = mora[i+2]  ### next next
          else:
              o = ''
          if o not in _OWARI:
              syllable.append(m + n)
              i += 2
          else:
              syllable.append(m)
              i += 1 
      else:
          syllable.append(m)
          i += 1

  return syllable


def expand_r(readings):
    """
    Take a list of readings, normalize them

    >>> expand_r(['ちい.さい'])
    ['ちいさい', 'ちい', 'さい']
    >>> expand_r(['こ-'])
    ['こ']
    """
    allr = []
    for r in readings:
        r = r.strip('-')
        # deal with '.' and '-'
        # ['ちい.さい', 'こ-', 'お-', 'さ-']
        if '.' in r:
            allr.append(r.replace('.', ''))
            allr += r.split('.')
        else:
            allr.append(r)
    return allr

