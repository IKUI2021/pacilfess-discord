from typing import Optional

from discord import Embed


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
        + " you can react with ❌ to vote for deletion. (or ping the mods)"
    )
    return embed
