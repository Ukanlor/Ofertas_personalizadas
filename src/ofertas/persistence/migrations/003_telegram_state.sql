CREATE TABLE telegram_state (
    key TEXT PRIMARY KEY CHECK (length(trim(key)) > 0),
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE telegram_callbacks (
    callback_query_id TEXT PRIMARY KEY CHECK (
        length(trim(callback_query_id)) > 0
    ),
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (length(trim(action)) > 0),
    target_id INTEGER NOT NULL,
    processed_at TEXT NOT NULL
);
