CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    canonical_title TEXT NOT NULL CHECK (length(trim(canonical_title)) > 0),
    normalized_title TEXT NOT NULL UNIQUE CHECK (length(normalized_title) > 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE aliases (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    alias TEXT NOT NULL CHECK (length(trim(alias)) > 0),
    normalized_alias TEXT NOT NULL UNIQUE CHECK (length(normalized_alias) > 0),
    created_at TEXT NOT NULL
);

CREATE INDEX aliases_game_id_idx ON aliases(game_id);

CREATE TABLE variants (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (length(platform) > 0),
    edition TEXT NOT NULL,
    format TEXT NOT NULL,
    region TEXT NOT NULL,
    drm TEXT NOT NULL,
    condition TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (game_id, platform, edition, format, region, drm, condition)
);

CREATE INDEX variants_game_id_idx ON variants(game_id);
