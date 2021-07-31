from datetime import datetime
from typing import Iterable, TypeVar, Type, Optional, Union

from dataclasses_json import DataClassJsonMixin

import aiosqlite
import discord
from pacilfess_discord.models import BannedUser
from pacilfess_discord.helper.hasher import hash_user

T = TypeVar("T", bound=DataClassJsonMixin)


class DBHelper:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.db.row_factory = aiosqlite.Row

    async def execute(self, sql: str, parameters: Iterable = None):
        cur = await self.db.cursor()
        await cur.execute(sql, parameters)
        await cur.close()
        await self.db.commit()

    async def fetchone(
        self,
        cls: Type[T],
        sql: str,
        parameters: Iterable = None,
    ) -> Optional[T]:
        cur = await self.db.execute(sql, parameters)
        result = await cur.fetchone()
        await cur.close()

        if not result:
            return None

        return cls.from_dict(dict(result))

    async def fetchall(
        self,
        cls: Type[T],
        sql: str,
        parameters: Iterable = None,
    ) -> Iterable[T]:
        cur = await self.db.execute(sql, parameters)
        result = await cur.fetchall()
        await cur.close()

        if not result:
            return []

        return [cls.from_dict(dict(res)) for res in result]

    async def close(self):
        await self.db.close()

    async def check_banned(self, user: Union[discord.Member, str]):
        current_time = datetime.now()

        if isinstance(user, str):
            user_hash = user
        else:
            user_hash = hash_user(user)

        res = await self.fetchone(
            BannedUser,
            "SELECT * FROM banned_users WHERE id=?",
            parameters=(user_hash,),
        )
        if res:
            lift_datetime = res.datetime
            if current_time < lift_datetime:
                return res
            else:
                # We already get past the lifting time, so remove our entry from DB.
                await self.execute(
                    "DELETE FROM banned_users WHERE id=?",
                    parameters=(user_hash,),
                )

        return None
