# Pacilfess (Discord)

## Installing

-   Install [Poetry](https://python-poetry.org/).
-   Run `poetry install`.
-   Create a new `config.json` file with the following format.

```json
{
    "cogs": ["pacilfess_discord.cogs.Fess"],
    "db_path": "",
    "admins": [],
    "channel_id": 0000000000000,
    "token": ""
}
```

-   Fill in `admins` with list of Discord user IDs, and `channel_id` with the target channel ID.
-   Create an empty file, and run `database.sql` to that database.

## Running

-   Run `poetry run run.py`.
