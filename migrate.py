import asyncio
from typing import List
from pacilfess_discord.helper.database import database
from pacilfess_discord.models import BannedUser, ServerConfig, Violation, Confess
import aiosqlite

import json

"""
CREATE TABLE confessions (
    message_id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    sendtime INTEGER NOT NULL,
    attachment TEXT
);
CREATE TABLE banned_users (
    id TEXT PRIMARY KEY,
    timeout INTEGER NOT NULL
);
CREATE TABLE violations (
    user_hash TEXT NOT NULL,
    severity INTEGER NOT NULL,
    timestamp INTEGER NOT NULL
);
"""

with open("old_config.json", "r") as f:
    config = json.load(f)


async def migrate_banned_users(conn: aiosqlite.Connection):
    rows = await conn.execute_fetchall("SELECT * FROM banned_users")
    new_objs: List[BannedUser] = []
    for row in rows:
        new_objs.append(
            BannedUser(
                user_id=row[0],
                server_id=config["guild_id"],
                timeout=row[1],
            )
        )

    if new_objs:
        await BannedUser.objects.bulk_create(new_objs)


async def migrate_confessions(conn: aiosqlite.Connection):
    rows = await conn.execute_fetchall("SELECT * FROM confessions")
    new_objs: List[Confess] = []
    for row in rows:
        new_objs.append(
            Confess(
                server_id=config["guild_id"],
                message_id=row[0],
                user_id=row[2],
                content=row[1],
                sendtime=row[3],
                attachment=row[4],
            )
        )

    if new_objs:
        await Confess.objects.bulk_create(new_objs)


async def migrate_violations(conn: aiosqlite.Connection):
    rows = await conn.execute_fetchall("SELECT * FROM violations")
    new_objs: List[Violation] = []
    for row in rows:
        new_objs.append(
            Violation(
                user_id=row[0],
                server_id=config["guild_id"],
                severity=row[1],
                timestamp=row[2],
            )
        )

    if new_objs:
        await Violation.objects.bulk_create(new_objs)


async def create_config():
    await ServerConfig.objects.create(
        server_id=config["guild_id"],
        votelog_channel=config["log_channel_id"],
        confession_channel=config["channel_id"],
        admin_roles=config["admin_roles"],
        minimum_vote=config["minimum_vote"],
    )


async def run():
    await database.connect()
    async with aiosqlite.connect("old.db") as db:
        await migrate_banned_users(db)
        await migrate_confessions(db)
        await migrate_violations(db)
    await create_config()
    await database.disconnect()


asyncio.run(run())
