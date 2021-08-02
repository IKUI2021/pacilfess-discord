from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

import aiohttp
from discord.ext.commands import Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from pacilfess_discord.config import config
from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.hasher import hash_user
from pacilfess_discord.helper.regex import DISCORD_RE
from pacilfess_discord.models import Confess

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess as FessBot


class Fess(Cog):
    def __init__(self, bot: "FessBot"):
        self.bot = bot

    async def _check_attachment(self, url: str):
        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                async with session.head(url) as resp:
                    resp.raise_for_status()
                    return resp.headers["Content-Type"].startswith("image")
        except Exception:
            return False

    @cog_ext.cog_slash(
        name="confess",
        description="Submits a confession.",
        guild_ids=[config.guild_id],
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
        current_time = datetime.now()

        # Check if sender is banned or not.
        banned_data = await self.bot.db.check_banned(ctx.author)
        if banned_data:
            await ctx.send(
                "You are banned from sending a confession until "
                + f"`{banned_data.datetime.isoformat(' ', 'seconds')}`.",
                hidden=True,
            )
            return

        if attachment and not await self._check_attachment(attachment):
            await ctx.send(
                "Invalid attachment given! It can only be image.",
                hidden=True,
            )
            return

        embed = create_embed(confession, attachment)
        fess_message = await self.bot.target_channel.send(embed=embed)
        await fess_message.add_reaction("❌")

        # Save to database for moderation purposes.
        await self.bot.db.execute(
            "INSERT INTO confessions(message_id, content, author, sendtime, attachment) VALUES (?, ?, ?, ?, ?)",
            parameters=(
                fess_message.id,
                confession,
                hash_user(ctx.author),
                current_time.timestamp(),
                attachment,
            ),
        )
        await ctx.send("Done!", hidden=True)

    @cog_ext.cog_slash(
        name="delete",
        description="Deletes a confession.",
        guild_ids=[config.guild_id],
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
        current_time = datetime.now()
        five_mins_ago = current_time - timedelta(minutes=5)
        if link:
            re_result = DISCORD_RE.search(link)
            if not re_result:
                await ctx.send("Invalid confession link!", hidden=True)
                return

            confess = await self.bot.db.fetchone(
                Confess,
                "SELECT * FROM confessions "
                + "WHERE author=? AND sendtime>=? AND message_id=? "
                + "ORDER BY sendtime DESC",
                parameters=(
                    hash_user(ctx.author),
                    five_mins_ago.timestamp(),
                    int(re_result.group("MESSAGE")),
                ),
            )
        else:
            confess = await self.bot.db.fetchone(
                Confess,
                "SELECT * FROM confessions "
                + "WHERE author=? AND sendtime>=? "
                + "ORDER BY sendtime DESC",
                parameters=(hash_user(ctx.author), five_mins_ago.timestamp()),
            )

        if not confess:
            await ctx.send(
                "No confession earlier than 5 minutes ago found.",
                hidden=True,
            )
            return

        confess_id: int = confess.message_id
        confess_msg = await self.bot.target_channel.fetch_message(confess_id)
        await confess_msg.edit(
            embed=create_embed("*This confession has been deleted by the author.*")
        )

        await self.bot.db.execute(
            "DELETE FROM confessions WHERE message_id=?",
            parameters=(confess_id,),
        )
        await ctx.send("Done!", hidden=True)


def setup(bot: "FessBot"):
    bot.add_cog(Fess(bot))
