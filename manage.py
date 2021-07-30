from pacilfess_discord.config import config

import os
import sqlite3
import importlib.util


def get_db():
    rv = sqlite3.connect(config.db_path)
    return rv


def migrate_sql(db: sqlite3.Connection, path: str):
    with open(path, mode="r") as f:
        db.cursor().executescript(f.read())


def migrate_py(db: sqlite3.Connection, path: str):
    spec = importlib.util.spec_from_file_location("migrate.db", path)
    migrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migrator)
    migrator.run(db)


def migrate_db():
    def get_script_version(path):
        return int(os.path.basename(path).split("_")[0])

    db = get_db()
    current_version = db.cursor().execute("pragma user_version").fetchone()[0]
    print("Current version:", current_version)

    directory = os.path.dirname(__file__)
    migrations_path = os.path.join(directory, "migrations")
    migration_files = list(os.listdir(migrations_path))
    for migration in sorted(migration_files):
        path = os.path.join(migrations_path, migration)
        if not os.path.isfile(path):
            continue

        migration_version = get_script_version(path)
        if migration_version > current_version:
            print("Applying:", migration)
            if path.endswith("sql"):
                migrate_sql(db, path)
            else:
                migrate_py(db, path)
            db.cursor().execute("PRAGMA user_version=" + str(migration_version))

    new_version = db.cursor().execute("pragma user_version").fetchone()[0]
    print("New version:", new_version)


if __name__ == "__main__":
    migrate_db()
