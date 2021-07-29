import re

DISCORD_RE = re.compile(
    r"http[s]?:\/\/discord\.com\/channels\/(?P<GUILD>[0-9]+)\/(?P<CHANNEL>[0-9]+)\/(?P<MESSAGE>[0-9]+)"
)
ETA_RE = re.compile(
    r"(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?"
)
