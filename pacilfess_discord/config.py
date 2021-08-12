import json
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Config(DataClassJsonMixin):
    db_path: str
    token: str
    default_vote: int
    secret: str

    @property
    def db_url(self):
        return f"sqlite:///{self.db_path}"


with open("config.json", "r") as f:
    config = Config.from_dict(json.load(f))
