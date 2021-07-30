import sqlite3
from hashlib import sha256

table_script = """
DROP TABLE confessions;
CREATE TABLE confessions (
    message_id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    sendtime INTEGER NOT NULL,
    attachment TEXT
);

DROP TABLE banned_users;
CREATE TABLE banned_users (
    id TEXT PRIMARY KEY,
    timeout INTEGER NOT NULL
);
"""


def run(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT * FROM confessions")
    confessions = cur.fetchall()
    cur.close()

    cur = conn.cursor()
    cur.execute("SELECT * FROM banned_users")
    banned_users = cur.fetchall()
    cur.close()

    conn.executescript(table_script)
    conn.commit()

    cur = conn.cursor()
    new_fess = []
    for fess in confessions:
        hasher = sha256(str(fess[2]).encode())
        user_hash = hasher.hexdigest()
        new_fess.append((fess[0], fess[1], user_hash, fess[4], fess[5]))

    conn.executemany("INSERT INTO confessions VALUES (?, ?, ?, ?, ?)", new_fess)
    conn.commit()

    cur = conn.cursor()
    new_users = []
    for u in banned_users:
        hasher = sha256(str(u[0]).encode())
        user_hash = hasher.hexdigest()
        new_users.append((user_hash, u[2]))

    conn.executemany("INSERT INTO banned_users VALUES (?, ?)", new_users)
    conn.commit()
