import json
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Config(DataClassJsonMixin):
    db_path: str
    admins: List[int]
    admin_roles: List[int]
    channel_id: int
    token: str
    guild_id: int
    minimum_vote: int
    log_channel_id: Optional[int]
    secret: str


with open("config.json", "r") as f:
    config = Config.from_dict(json.load(f))
