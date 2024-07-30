-- SQLite
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  hash TEXT NOT NULL,
  cash NUMERIC NOT NULL DEFAULT 50
);

CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE bets (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  game_id TEXT NOT NULL,
  outcome REAL NOT NULL,
  amount NUMERIC NOT NULL,
  result TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);