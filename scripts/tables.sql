-- Information about the names
CREATE TABLE namae (nid  INTEGER primary key,
       	     	   year INTEGER,
		   orth TEXT, 
		   pron TEXT,
		   loc TEXT,
		   gender TEXT,
		   explanation TEXT,
		   src TEXT);

CREATE TABLE nrank (nrid  INTEGER primary key,
       	     	   year INTEGER,  -- year
		   orth TEXT,     -- written form
		   pron TEXT,	  -- pronunciation (in hiragana)
		   rank INTEGER,     -- 1 is most frequent, same frequency are tied
		   gender TEXT,   -- M or F
		   freq INTEGER,     -- how often it occurs
		   src TEXT);     -- source: hs, meiji, ..

CREATE TABLE name_year_cache (
       -- src is 
       --   bc, hs are totals of all instances
       --   meiji  (total of the top 50/100 instances)
       --   totals (total for meiji from API)	
       --   births (total number of births)
       src TEXT,     -- where it's from
       dtype TEXT,   -- dtype orth|pron|both|total|birth
       year INTEGER, -- year
       gender TEXT,
       count INTEGER, -- how many
       PRIMARY KEY (src, dtype, year, gender)
    );

-- Information about the different orthographies
CREATE TABLE orth (orth_id INTEGER primary key,
       orth TEXT,  --- orthography
       script TEXT --- which script is the text 
       );

-- Information about the different phonological forms
-- mora and syllables are separated by spaces
CREATE TABLE pron (pron_id INTEGER primary key,
       pron TEXT,  -- pronunciation
       mora TEXT,  -- the pronunciation split into mora
       syll TEXT   -- the pronunciation split into syllables	
       );
       
-- Information about the orth-pron mapping
-- e.g. 日乃世 ひのせ 日/ひ/kun 乃/の/kun 世/せ/on
--      春椛 はるか 春/はる/kun 椛//irregular
CREATE TABLE mapp (mapp_id INTEGER primary key,
       pron TEXT,   -- pronunciation
       orth TEXT,   -- orthography	
       mapping TEXT -- the mapping split into characters	
       );


CREATE TABLE attr (nid  INTEGER NOT NULL,
      olength INTEGER, --length of name
      plength INTEGER, --length of pronunciation
      mlength INTEGER, --length in mora
      slength INTEGER, --length in syllables			
      char1 TEXT,      -- first character in name
      char_1 TEXT,     -- last character in name
      char_2 TEXT,     -- second to last character in name
      mora1 TEXT,      -- first mora in pronuncation
      mora_1 TEXT,     -- last mora in pronuncation
      mora_2 TEXT,     -- second to last mora in pronuncation
      syll1 TEXT,      -- first mora in pronunciation
      syll_1 TEXT,     -- last syllable in pronunciation
      syll_2 TEXT,     -- second to last syllable in pronuncation
      uni_ch TEXT,     -- single character name
      script TEXT,     -- kata, hira, kanji, mix
      Foreign KEY (nid) REFERENCES namae (nid));

CREATE TABLE ntok (
        nid INTEGER, ---
	kid INTEGER, ---
	Foreign KEY (nid) REFERENCES namae (nid),
	Foreign KEY (kid) REFERENCES kanji (kid));

CREATE TABLE kanji (kid  INTEGER primary key,
       kanji TEXT,    --- kanji
       yfrom INTEGER,  --- year it was used from
       grade INTEGER, 
       freq INTEGER,
       imi TEXT,
       mean TEXT,
       kunyomi TEXT,
       onyomi TEXT,
       other TEXT,
       nanori TEXT,
       scount INTEGER);


-- Create a view that combines names from Heisei and Baby Calendar
-- with Baby Calendar names aggregated to either 2012 or 2019
CREATE VIEW combined AS

-- Names from Heisei (hs) - include all as they are
SELECT 
    nid,
    year,
    orth,
    pron,
    gender,
    'hs+bc' AS src
FROM 
    namae
WHERE 
    namae.src = 'hs'

UNION ALL
-- Names from Baby Calendar (bc) - aggregate by year
SELECT 
    nid,
    CASE 
        WHEN year < 2015 THEN 2011
        ELSE 2019
    END AS year,
    orth,
    pron,
    gender,
    'hs+bc' AS src
    FROM 
    namae
WHERE 
    namae.src = 'bc';

