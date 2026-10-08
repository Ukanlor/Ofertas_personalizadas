CREATE TABLE preferences (
    game_id INTEGER PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,
    interest_score INTEGER CHECK (
        interest_score IS NULL OR interest_score BETWEEN 0 AND 10
    ),
    updated_at TEXT NOT NULL
);

CREATE TABLE ownership (
    variant_id INTEGER PRIMARY KEY REFERENCES variants(id) ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (length(trim(source)) > 0),
    acquired_at TEXT,
    updated_at TEXT NOT NULL
);
