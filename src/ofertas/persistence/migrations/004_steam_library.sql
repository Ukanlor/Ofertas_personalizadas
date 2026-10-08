CREATE TABLE steam_profile (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    steam_id TEXT NOT NULL UNIQUE CHECK (length(trim(steam_id)) > 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE steam_apps (
    app_id INTEGER PRIMARY KEY CHECK (app_id > 0),
    variant_id INTEGER NOT NULL UNIQUE
        REFERENCES variants(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    playtime_forever_minutes INTEGER NOT NULL
        CHECK (playtime_forever_minutes > 0),
    playtime_recent_minutes INTEGER NOT NULL DEFAULT 0
        CHECK (playtime_recent_minutes >= 0),
    last_played_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE INDEX steam_apps_last_seen_at_idx ON steam_apps(last_seen_at);
