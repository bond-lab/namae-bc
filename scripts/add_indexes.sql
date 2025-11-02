CREATE INDEX IF NOT EXISTS idx_namae_src ON namae(src);
CREATE INDEX IF NOT EXISTS idx_namae_gender ON namae(gender);
CREATE INDEX IF NOT EXISTS idx_namae_orth ON namae(orth);
CREATE INDEX IF NOT EXISTS idx_namae_pron ON namae(pron);

CREATE INDEX IF NOT EXISTS idx_attr_nid ON attr(nid);
CREATE INDEX IF NOT EXISTS idx_ntok_nid ON ntok(nid);
CREATE INDEX IF NOT EXISTS idx_ntok_kid ON ntok(kid);
