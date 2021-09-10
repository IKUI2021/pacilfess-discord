from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, Optional, cast

import aiohttp
import discord
from discord.channel import TextChannel
from discord.ext.commands import Cog, guild_only
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.hasher import hash_user
from pacilfess_discord.helper.regex import DISCORD_RE
from pacilfess_discord.helper.utils import check_banned
from pacilfess_discord.models import Confess, ServerConfig

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess as FessBot


class Fess(Cog):
    def __init__(self, bot: "FessBot"):
        self.bot = bot
        self.last_timestamp: Dict[str, float] = {}

    async def _check_attachment(self, url: str):
        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                async with session.head(url) as resp:
                    resp.raise_for_status()
                    return resp.headers["Content-Type"].startswith("image")
        except Exception:
            return False

    async def _get_reply(
        self, ctx: SlashContext, target_channel: TextChannel, confession: str
    ):
        link = DISCORD_RE.search(confession)
        if link:
            start, end = link.span()
            if start == 0 or end == len(confession):
                message_id = int(link.group("MESSAGE"))

                # Ensure message actually exists and is in confess channel.
                confess = await Confess.objects.get_or_none(
                    server_id=ctx.guild_id,
                    message_id=message_id,
                )
                if not confess:
                    return None

                message_ref = discord.MessageReference(
                    message_id=message_id,
                    channel_id=target_channel.id,
                )
                return message_ref
        return None

    @cog_ext.cog_slash(
        name="confess",
        description="Submits a confession.",
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
    @guild_only()
    async def _confess(
        self,
        ctx: SlashContext,
        confession: str,
        attachment: Optional[str] = None,
    ):
        await ctx.defer(hidden=True)

        confession = confession.strip()
        current_time = datetime.now()
        user_hash = hash_user(ctx.author)

        # Check if server is configured.
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild_id)
        if not server_conf.confession_channel:
            return await ctx.send(
                "This server has not been configured. Please contact the server admin.",
                hidden=True,
            )

        # Check server cooldown
        if server_conf.cooldown_time:
            if user_hash in self.last_timestamp:
                last_time = self.last_timestamp[user_hash]
                delta = current_time.timestamp() - last_time
                if delta < server_conf.cooldown_time:
                    eta = int(server_conf.cooldown_time - delta)
                    return await ctx.send(
                        (
                            "Server is in cooldown mode, "
                            + f"you may send a confession again after {eta} seconds."
                        ), hidden=True
                    )
            self.last_timestamp[user_hash] = current_time.timestamp()

        # Fetch the target channel, and check if it exists.
        target_channel = cast(
            Optional[TextChannel], self.bot.get_channel(server_conf.confession_channel)
        )
        if not target_channel:
            return await ctx.send(
                "Cannot seem to find confession channel. Maybe it was deleted?",
                hidden=True,
            )

        # Check if sender is banned or not.
        banned_data = await check_banned(user_hash, ctx.guild_id)
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

        raw_confession = confession
        reply = await self._get_reply(ctx, target_channel, confession)
        if reply:
            confession = DISCORD_RE.sub("", confession).strip()
            if not confession:
                await ctx.send("Please send a message!", hidden=True)
                return

        embed = create_embed(confession, attachment)
        fess_message = await target_channel.send(
            embed=embed, reference=reply, mention_author=False
        )
        await fess_message.add_reaction("❌")

        # Save to database for moderation purposes.
        await Confess.objects.create(
            server_id=ctx.guild_id,
            message_id=fess_message.id,
            user_id=user_hash,
            content=raw_confession,
            sendtime=current_time.timestamp(),
            attachment=attachment,
        )
        await ctx.send("Done!", hidden=True)

    @cog_ext.cog_slash(
        name="delete",
        description="Deletes a confession.",
        options=[
            create_option(
                name="link",
                description="Confession's message url to remove.",
                option_type=3,
                required=False,
            )
        ],
    )
    @guild_only()
    async def _delete_fess(self, ctx: SlashContext, link: Optional[str] = None):
        await ctx.defer(hidden=True)

        current_time = datetime.now()
        user_hash = hash_user(ctx.author)
        five_mins_ago = current_time - timedelta(minutes=5)

        # Check if server is configured.
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild_id)
        if not server_conf.confession_channel:
            return await ctx.send(
                "This server has not been configured. Please contact the server admin.",
                hidden=True,
            )

        # Fetch the target channel, and check if it exists.
        confession_channel = cast(
            Optional[TextChannel], self.bot.get_channel(server_conf.confession_channel)
        )
        if not confession_channel:
            return await ctx.send(
                "Cannot seem to find confession channel. Maybe it was deleted?",
                hidden=True,
            )

        if link:
            re_result = DISCORD_RE.search(link)
            if not re_result:
                await ctx.send("Invalid confession link!", hidden=True)
                return

            confess = await Confess.objects.order_by("-sendtime").get_or_none(
                server_id=ctx.guild_id,
                message_id=int(re_result.group("MESSAGE")),
                user_id=user_hash,
                sendtime__gt=five_mins_ago.timestamp(),
            )
        else:
            # If link is not found, check the last 5 mins for confess and
            # pick the LATEST one
            confess = (
                await Confess.objects.order_by("-sendtime")
                .limit(1)
                .get_or_none(
                    server_id=ctx.guild_id,
                    user_id=user_hash,
                    sendtime__gt=five_mins_ago.timestamp(),
                )
            )

        if not confess:
            await ctx.send(
                "No confession earlier than 5 minutes ago found.",
                hidden=True,
            )
            return

        confess_id: int = confess.message_id
        confess_msg = await confession_channel.fetch_message(confess_id)
        await confess_msg.edit(
            embed=create_embed(
                "*This confession has been deleted by the author.*",
                use_quote=False,
            )
        )

        await confess.delete()
        await ctx.send("Done!", hidden=True)


def setup(bot: "FessBot"):
    bot.add_cog(Fess(bot))
