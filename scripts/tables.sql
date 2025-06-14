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
      syll1 TEXT,      -- first mora in pronuncation
      syll_1 TEXT,     -- last mora in pronuncation
      syll_2 TEXT,     -- second to last mora in pronuncation
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

CREATE TABLE name_year_cache (
       src TEXT,     -- where its from
       dtype TEXT,   -- dtype orth|pron|both|total|birth
       year INTEGER, -- year
       gender TEXT,
       count INTEGER, -- how many
       PRIMARY KEY (src, dtype, year, gender)
    );


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

