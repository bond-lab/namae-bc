-- Indexes for namae (14.7M rows — single-column indexes on low-cardinality
-- columns like src and gender are not useful; compound indexes are needed)
CREATE INDEX IF NOT EXISTS idx_namae_src_year_gender ON namae(src, year, gender);
CREATE INDEX IF NOT EXISTS idx_namae_src_orth        ON namae(src, orth);
CREATE INDEX IF NOT EXISTS idx_namae_src_pron        ON namae(src, pron);

-- Indexes for nrank (1.5M rows — the most heavily queried table, currently
-- has no indexes at all)
CREATE INDEX IF NOT EXISTS idx_nrank_src_year_gender ON nrank(src, year, gender);
CREATE INDEX IF NOT EXISTS idx_nrank_src_orth        ON nrank(src, orth);
CREATE INDEX IF NOT EXISTS idx_nrank_src_pron        ON nrank(src, pron);

-- Indexes for attr and ntok (JOIN tables)
CREATE INDEX IF NOT EXISTS idx_attr_nid  ON attr(nid);
CREATE INDEX IF NOT EXISTS idx_ntok_nid  ON ntok(nid);
CREATE INDEX IF NOT EXISTS idx_ntok_kid  ON ntok(kid);

-- Indexes for mapp (used in irregular reading lookups)
CREATE INDEX IF NOT EXISTS idx_mapp_orth_pron ON mapp(orth, pron);

-- Indexes for kanji (character lookups)
CREATE INDEX IF NOT EXISTS idx_kanji_kanji ON kanji(kanji);

-- Covering indexes for androgyny/overlap queries (GROUP BY year, orth/pron)
CREATE INDEX IF NOT EXISTS idx_nrank_src_gender_year_orth ON nrank(src, gender, year, orth);
CREATE INDEX IF NOT EXISTS idx_nrank_src_gender_year_pron ON nrank(src, gender, year, pron);

-- name_year_cache already has PRIMARY KEY (src, dtype, year, gender)
-- which covers all its query patterns
