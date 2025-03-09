-- Information about the names
CREATE TABLE namae (nid  INTEGER primary key,
       	     	   year INTEGER,
		   orth TEXT, 
		   pron TEXT,
		   loc TEXT,
		   gender TEXT,
		   explanation TEXT,
		   src TEXT);

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
