# General Bugs

* phenomena/diversity.html is not working
* Names shows both Name and Pron as None for Meiji-orth
* Names shows nothing for Meiji-pron
** make it work properly
* Should add that Meiji is only last N years
* documentation should either link to data/README.mf and ATRRIBUTION.md or duplicate
** maybe split into sub entries: Morae/Syllables, Features, Data, Licenses, Download 
* add a feature Show Book (defaults to false)
** only show extra tables in features and Book menu if True


# Issues to Address for Zenodo Archiving

### Placeholder DOIs (fill in when known)
- `.zenodo.json` line 29: `"identifier": "10.xxxx/book-doi-placeholder"`
- `ATTRIBUTIONS.md` line 62: `https://doi.org/10.xxxx/zenodo.xxxxx`

### Incomplete book reference
- `ATTRIBUTIONS.md` line 68: marked as FIXME, needs full citation

### Install.md is server-specific
- Contains paths specific to `compling.upol.cz`; fine as-is if understood
  as deployment notes for that server
