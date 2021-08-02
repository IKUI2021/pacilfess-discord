from typing import Optional

from discord import Embed


def create_embed(
    confession: str,
    attachment: Optional[str] = None,
    footer: Optional[str] = None,
):
    confession_content = "> " + "\r\n> ".join(confession.splitlines()).strip()
    embed = Embed(
        title="Anonymous confession",
        description=confession_content,
    )
    if attachment:
        embed.set_image(url=attachment)

    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(
            text="If this confession breaks the rule,"
            + " you can react with ❌ to vote for deletion. (or ping the mods)"
        )
    return embed
