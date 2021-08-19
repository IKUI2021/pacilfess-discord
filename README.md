# Pacilfess (Discord)

# Information

While I try to make this as general as possible, some things might be a bit technical.

## What is this?

Pacilfess is a Discord bot that sends a confession (or actually--message) anonymously to a channel. That is all.

## How does it work?

Please look at [the wiki](/wiki).

---

# Developing

## Installing

-   Install [Poetry](https://python-poetry.org/).
-   Run `poetry install`.
-   Create a new `config.json` file with the following format.

```json
{
    "db_path": "data.db",
    "admins": [],
    "admin_roles": [],
    "channel_id": 00000000000000,
    "guild_id": 00000000000000,
    "minimum_vote": 5,
    "token": "",
    "log_channel_id": 00000000000000
}
```

-   Fill in `admins` with list of Discord user IDs, and `channel_id` with the target channel ID.
-   Create an empty file, and run `database.sql` to that database.

## Running

-   Run `poetry run run.py`.

## TODO

-   Add checks on `/fessmin`
