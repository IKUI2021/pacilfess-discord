from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import ormar
from dataclasses_json import DataClassJsonMixin

from pacilfess_discord.config import config
from pacilfess_discord.helper.database import database, metadata


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Confess(ormar.Model):
    class Meta(BaseMeta):
        tablename = "confessions"

    id: int = ormar.Integer(primary_key=True)
    server_id: int = ormar.Integer()
    message_id: int = ormar.Integer()
    user_id: str = ormar.Text()

    content: str = ormar.Text()
    sendtime: int = ormar.Integer()
    attachment: Optional[str] = ormar.Text(nullable=True)

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.sendtime)


class BannedUser(ormar.Model):
    class Meta(BaseMeta):
        tablename = "banned_users"

    id: int = ormar.Integer(primary_key=True)
    user_id: str = ormar.Text()
    server_id: int = ormar.Integer()

    timeout: int = ormar.Integer()

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timeout)


class Violation(ormar.Model):
    class Meta(BaseMeta):
        tablename = "violations"

    id: int = ormar.Integer(primary_key=True)
    user_id: str = ormar.Text()
    server_id: int = ormar.Integer()

    severity: int = ormar.Integer()
    timestamp: int = ormar.Integer()

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)


class ServerConfig(ormar.Model):
    class Meta(BaseMeta):
        tablename = "server_configs"

    server_id: int = ormar.Integer(primary_key=True)
    votelog_channel: Optional[int] = ormar.Integer(nullable=True)
    confession_channel: Optional[int] = ormar.Integer(nullable=True)
    admin_roles: List[int] = ormar.JSON(default="[]")
    minimum_vote: int = ormar.Integer(default=config.default_vote)


@dataclass
class DeletedData(DataClassJsonMixin):
    uid: str
    mid: int
    sid: int
