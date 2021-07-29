import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from discord.ext.commands import Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option
from pacilfess_discord.helper.embed import create_embed

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess as FessBot

DISCORD_RE = re.compile(
    r"http[s]?:\/\/discord\.com\/channels\/(?P<GUILD>[0-9]+)\/(?P<CHANNEL>[0-9]+)\/(?P<MESSAGE>[0-9]+)"
)


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
        res = await self.bot.db.fetchone(
            "SELECT * FROM banned_users WHERE id=?", (ctx.author_id,)
        )
        if res:
            ctx.send("You are banned from sending a confession.")
            return

        current_time = datetime.now()
        embed = create_embed(confession, attachment)
        fess_message = await self.bot.target_channel.send(embed=embed)

        # Save to database for moderation purposes.
        await self.bot.db.execute(
            "INSERT INTO confessions VALUES (?, ?, ?, ?, ?)",
            (
                fess_message.id,
                confession,
                ctx.author_id,
                ctx.author.name,
                current_time.timestamp(),
            ),
        )
        await ctx.send("Done!", hidden=True)

    @cog_ext.cog_slash(
        name="delete",
        description="Deletes a confession.",
        guild_ids=[863499218449858570],
        options=[
            create_option(
                name="link",
                description="Confession's message url to remove.",
                option_type=3,
                required=False,
            )
        ],
    )
    async def _delete_fess(self, ctx: SlashContext, link: Optional[str] = None):
        # https://discord.com/channels/<GUILD_ID>/<CHANNEL_ID>/<MESSAGE_ID>
        current_time = datetime.now()
        five_mins_ago = current_time - timedelta(minutes=5)
        if link:
            re_result = DISCORD_RE.search(link)
            if not re_result:
                await ctx.send("Invalid confession link!", hidden=True)
                return

            confess = await self.bot.db.fetchone(
                "SELECT * FROM confessions "
                + "WHERE author=? AND sendtime>=? AND message_id=? "
                + "ORDER BY sendtime DESC",
                (
                    ctx.author_id,
                    five_mins_ago.timestamp(),
                    int(re_result.group("MESSAGE")),
                ),
            )
        else:
            confess = await self.bot.db.fetchone(
                "SELECT * FROM confessions "
                + "WHERE author=? AND sendtime>=? "
                + "ORDER BY sendtime DESC",
                (ctx.author_id, five_mins_ago.timestamp()),
            )

        if not confess:
            await ctx.send(
                "No confession earlier than 5 minutes ago found.",
                hidden=True,
            )
            return

        confess_id: int = confess[0]
        confess_msg = await self.bot.target_channel.fetch_message(confess_id)
        await confess_msg.edit(
            embed=create_embed("*This confession has been deleted by the author.*")
        )

        await self.bot.db.execute(
            "DELETE FROM confessions WHERE message_id=?",
            (confess_id,),
        )
        await ctx.send("Done!", hidden=True)


def setup(bot: "FessBot"):
    bot.add_cog(Fess(bot))
