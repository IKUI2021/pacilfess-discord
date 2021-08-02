from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Confess(DataClassJsonMixin):
    message_id: int
    content: str
    author: str
    sendtime: int
    attachment: Optional[str]

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.sendtime)


@dataclass
class BannedUser(DataClassJsonMixin):
    id: str
    timeout: int

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timeout)


@dataclass
class Violation(DataClassJsonMixin):
    user_hash: str
    severity: int
    timestamp: int

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)


@dataclass
class DeletedData(DataClassJsonMixin):
    uid: str
    mid: int
