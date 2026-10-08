CREATE TABLE steam_import_exclusions (
    app_id INTEGER PRIMARY KEY CHECK (app_id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
