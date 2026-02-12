# -*- coding: utf-8 -*-

import os

#REPO_NAME = "myweb"  # Used for FREEZER_BASE_URL
DEBUG = True

# Assumes the app is located in the same directory
# where this file resides
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Default database option
DEFAULT_DB_OPTION = 'bc'

def parent_dir(path):
    '''Return the parent of a directory.'''
    return os.path.abspath(os.path.join(path, os.pardir))

PROJECT_ROOT = parent_dir(APP_DIR)
# In order to deploy to Github pages, build the static files to 'docs'

FREEZER_DESTINATION =  os.path.join(PROJECT_ROOT, 'docs')

# Since this is a repo page (not a Github user page),
# we need to set the BASE_URL to the correct url as per GH Pages' standards
#FREEZER_BASE_URL = "http://localhost/".format(REPO_NAME)
# use relative URLS
FREEZER_RELATIVE_URLS = True
FREEZER_REMOVE_EXTRA_FILES = False  # IMPORTANT: If this is True, all app files
                                    # will be deleted when you run the freezer

# ---------------------------------------------------------------------------
# Route definitions — pure data, no Flask dependency.
# Imported by both web/routes.py and tests.
# ---------------------------------------------------------------------------

### [(feat1, feat2, name, (possible combinations)), ...
features = [
    ('char1', '', '1st Char.', ('bc', 'hs', 'meiji')),
    ('char_1', '', 'Last Char.', ('bc', 'hs', 'meiji')),
    ('char_2', 'char_1', 'Last 2 Chars', ('bc', 'hs', 'meiji')),
    ('mora1', '', '1st Mora', ('bc', 'meiji_p')),
    ('mora_1', '', 'Last Mora', ('bc', 'meiji_p')),
    ('mora_2', 'mora_1', 'Last 2. Moras', ('bc', 'meiji_p')),
    ('char_1', 'mora_1', 'Last Char. +  Mora', ('bc',)),
    ('char1', 'mora1', 'First Char. +  Mora', ('bc',)),
    ('syll1', '', '1st Syllable', ('bc', 'meiji_p')),
    ('syll_1', '', 'Last Syllable', ('bc', 'meiji_p')),
    ('syll_2', 'syll_1', 'Last 2. Syllables', ('bc', 'meiji_p')),
    ('char_1', 'syll_1', 'Last Char. +  Syllable', ('bc',)),
    ('char1', 'syll1', 'First Char. +  Syllable', ('bc',)),
    ('uni_ch', '', '1 Char. Name', ('bc', 'hs', 'meiji')),
    ('kanji', '', 'Kanji', ('bc', 'hs', 'meiji')),
]

overall = [
    ('script', '', 'Script', ('bc', 'hs', 'meiji')),
    ('olength', '', 'Length Char.', ('bc', 'hs', 'meiji')),
    ('mlength', '', 'Length Mora', ('bc', 'meiji_p')),
    ('slength', '', 'Length Syllables', ('bc', 'meiji_p')),
]

phenomena = [
    ('jinmei', '', 'Kanji for names'),
    ('redup', '', 'Reduplication'),
    ('irregular', '', 'Irregular Readings'),
    ('genderedness', '', 'Genderedness of names'),
    ('diversity', '', 'Diversity Measures'),
    ('overlap', '', 'Overlapping Names'),
    ('androgyny', '', 'Androgynous Names'),
    ('topnames', '', 'Top Names'),
]
