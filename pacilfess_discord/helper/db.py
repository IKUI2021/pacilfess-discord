from typing import Iterable
import aiosqlite


class DBHelper:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def execute(self, sql: str, parameters: Iterable = None):
        cur = await self.db.cursor()
        await cur.execute(sql, parameters)
        await cur.close()
        await self.db.commit()

    async def fetchone(self, sql: str, parameters: Iterable = None):
        cur = await self.db.execute(sql, parameters)
        result = await cur.fetchone()
        await cur.close()

        return result

    async def fetchmany(self, sql: str, parameters: Iterable = None):
        cur = await self.db.execute(sql, parameters)
        result = await cur.fetchmany()
        await cur.close()

        return result
