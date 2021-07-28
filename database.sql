CREATE TABLE confessions (
    message_id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    author INTEGER NOT NULL,
    author_name TEXT NOT NULL,
    sendtime INTEGER NOT NULL
);

CREATE TABLE banned_users (
    id INTEGER PRIMARY KEY,
    username REAL NOT NULL
);