# Pacilfess (Discord)

# Information

While I try to make this as general as possible, some things might be a bit technical.

## What is this?

Pacilfess is a Discord bot that sends a confession (or actually--message) anonymously to a channel. That is all.

## How does it work?

Please look at [the wiki](https://github.com/Ilmu-Komputer-UI-2021/pacilfess-discord/wiki).

---

# Developing

## Installing

-   Install [Poetry](https://python-poetry.org/).
-   Run `poetry install`.
-   Create a new `config.json` file with the following format.

```json
{
    "db_path": "",
    "default_vote": 1,
    "token": "",
    "secret": ""
}
```

-   Run `poetry run alembic upgrade head`.

## Running

-   Run `poetry run run.py`.

## TODO

Nothing here.
