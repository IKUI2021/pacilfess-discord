import json
from pacilfess_discord.typing import ConfigType

import os
import sqlite3

with open("config.json", "r") as f:
    config: ConfigType = json.load(f)


def get_db():
    rv = sqlite3.connect(config["db_path"])
    return rv


def migrate_db():
    def get_script_version(path):
        return int(path.split("_")[0].split("/")[1])

    db = get_db()
    current_version = db.cursor().execute("pragma user_version").fetchone()[0]
    print("Current version:", current_version)

    directory = os.path.dirname(__file__)
    migrations_path = os.path.join(directory, "migrations/")
    migration_files = list(os.listdir(migrations_path))
    for migration in sorted(migration_files):
        path = "migrations/{0}".format(migration)
        migration_version = get_script_version(path)

        if migration_version > current_version:
            print("Applying:", migration)
            with open(path, mode="r") as f:
                db.cursor().executescript(f.read())
                db.cursor().execute("PRAGMA user_version=" + str(migration_version))

    new_version = db.cursor().execute("pragma user_version").fetchone()[0]
    print("New version:", new_version)


if __name__ == "__main__":
    migrate_db()
