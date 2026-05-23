CREATE TABLE IF NOT EXISTS menu_votes (
  menu_id    INT PRIMARY KEY,
  vote_count INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_votes (
  session_id VARCHAR(64)  NOT NULL,
  menu_id    INT          NOT NULL,
  voted_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  PRIMARY KEY (session_id, menu_id)
);

-- seed all 20 menus with 0 votes
INSERT INTO menu_votes (menu_id) VALUES
  (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
  (11),(12),(13),(14),(15),(16),(17),(18),(19),(20)
ON CONFLICT DO NOTHING;
