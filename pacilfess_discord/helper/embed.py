from typing import Optional

from discord import Colour, Embed


def create_embed(
    confession: str,
    attachment: Optional[str] = None,
    footer: Optional[str] = None,
    use_quote: bool = True,
):
    if use_quote:
        confession_content = "> " + "\r\n> ".join(confession.splitlines()).strip()
    else:
        confession_content = confession

    color = Colour.random() if use_quote else Colour.red()
    embed = Embed(
        title="Anonymous Confession",
        description=confession_content,
        color=color,
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
