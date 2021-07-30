from typing import Iterable, TypeVar, Type, Optional

from dataclasses_json import DataClassJsonMixin

import aiosqlite

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
