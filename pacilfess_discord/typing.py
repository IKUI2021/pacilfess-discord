# This file will be used to assist type hinting.
from typing import List
from typing_extensions import TypedDict


class ConfigType(TypedDict):
    db_path: str
    admins: List[int]
    channel_id: int
    token: str
