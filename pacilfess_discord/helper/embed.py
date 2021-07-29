from discord import Embed
from typing import Optional


def create_embed(confession: str, attachment: Optional[str] = None):
    confession_content = "> " + confession
    embed = Embed(
        title="Anonymous confession",
        description=confession_content,
    )
    if attachment:
        embed.set_image(url=attachment)

    embed.set_footer(
        text="If this confession breaks the rule,"
        + ' you can report it using "/report [message link]"'
    )
    return embed
