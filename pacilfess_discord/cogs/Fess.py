from typing import Optional, TYPE_CHECKING
from discord import Embed
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from discord.ext.commands import Cog

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess as FessBot


def create_embed(confession, attachment):
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


class Fess(Cog):
    def __init__(self, bot: "FessBot"):
        self.bot = bot

    @cog_ext.cog_slash(
        name="confess",
        description="Submits a confession.",
        guild_ids=[863499218449858570],
        options=[
            create_option(
                name="confession",
                description="The confession text to be sent.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="attachment",
                description="Image URL to be attached.",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def _confess(
        self,
        ctx: SlashContext,
        confession: str,
        attachment: Optional[str] = None,
    ):
        # Check if sender is banned or not.
        cur = await self.bot.db.execute(
            "SELECT * FROM banned_users WHERE id=?", (ctx.author_id,)
        )
        if await cur.fetchone():
            ctx.send("You are banned from sending a confession.")
            return

        embed = create_embed(confession, attachment)
        fess_message = await self.bot.target_channel.send(embed=embed)

        # Save to database for moderation purposes.
        cur = await self.bot.db.cursor()
        await cur.execute(
            "INSERT INTO confessions VALUES (?, ?, ?, ?, ?)",
            (
                fess_message.id,
                confession,
                ctx.author_id,
                ctx.author.name,
                fess_message.created_at.timestamp(),
            ),
        )
        await self.bot.db.commit()
        await ctx.send("Done!", hidden=True)


def setup(bot: "FessBot"):
    bot.add_cog(Fess(bot))
