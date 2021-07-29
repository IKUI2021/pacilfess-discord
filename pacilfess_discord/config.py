import json
from typing import List
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin


@dataclass
class Config(DataClassJsonMixin):
    db_path: str
    admins: List[int]
    channel_id: int
    token: str
    guild_id: int


with open("config.json", "r") as f:
    config = Config.from_dict(json.load(f))
