import sys
import traceback
from datetime import datetime, timedelta
from typing import Union, cast, Optional

import discord
from discord.channel import TextChannel
from discord.ext import commands
from discord.ext.commands import Bot, Context
from discord.raw_models import RawReactionActionEvent
from discord.reaction import Reaction
from discord_slash import SlashCommand
from discord_slash.context import SlashContext

from pacilfess_discord.config import config
from pacilfess_discord.helper.database import database
from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.hasher import enc_data, hash_user
from pacilfess_discord.helper.utils import Forbidden, NoConfig, check_banned
from pacilfess_discord.models import (
    BannedUser,
    Confess,
    DeletedData,
    ServerConfig,
    Violation,
)

cogs = [
    "pacilfess_discord.cogs.Fess",
    "pacilfess_discord.cogs.Admin",
    "pacilfess_discord.cogs.Config",
]


class Fess(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slash = SlashCommand(self, sync_commands=True)
        for cog in cogs:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(
                    "Could not load extension {0} due to {1.__class__.__name__}: {1}".format(
                        cog, exc
                    )
                )

    async def on_vote_delete(self, confess: Confess):
        deleted_data = DeletedData(
            uid=confess.user_id,
            mid=confess.message_id,
            sid=confess.server_id,
        )
        encrypted = enc_data(deleted_data)
        embed = create_embed(
            confess.content + f"\r\n\r\nID: `${encrypted.decode('UTF-8')}`",
            attachment=confess.attachment,
            footer="To ban this user, use /fessmin muteid <ID>",
        )

        server_conf = await ServerConfig.objects.get_or_none(
            server_id=confess.server_id
        )
        if not server_conf or not server_conf.votelog_channel:
            return

        log_channel = cast(
            Optional[TextChannel], self.get_channel(server_conf.votelog_channel)
        )
        if log_channel:
            await log_channel.send("Confession deleted from vote:", embed=embed)

    async def on_sev_change(
        self, user: Union[discord.Member, str], server: Union[discord.Guild, int]
    ):
        current_time = datetime.now()
        month_ago = current_time - timedelta(weeks=4)

        if isinstance(user, str):
            user_hash = user
        else:
            user_hash = hash_user(user)

        if isinstance(server, discord.Guild):
            server_id = server.id
        else:
            server_id = server

        # Remove existing ban just to be safe.
        existing_ban = await check_banned(user_hash, server_id)
        if existing_ban:
            await existing_ban.delete()

        violations = await Violation.objects.all(
            user_id=user_hash,
            server_id=server_id,
            timestamp__gte=month_ago.timestamp(),
        )
        total_violations = sum([x.severity for x in violations])
        minutes = total_violations ** 2 * 30

        end_dt = current_time + timedelta(minutes=minutes)
        await BannedUser.objects.create(
            user_id=user_hash,
            server_id=server_id,
            timeout=end_dt.timestamp(),
        )

    async def on_raw_reaction_add(self, event: RawReactionActionEvent):
        confess = await Confess.objects.get_or_none(
            server_id=event.guild_id, message_id=event.message_id
        )
        if not confess:
            return

        server_conf = await ServerConfig.objects.get(server_id=event.guild_id)
        confession_channel: TextChannel = cast(
            TextChannel, self.get_channel(event.channel_id)
        )
        message = await confession_channel.fetch_message(event.message_id)

        # OK I legit don't know why is Reaction.emoji here is an str but on the event object,
        # its a PartialEmoji, kinda makes it a huge pain in the ass to be honest.
        reaction = cast(Reaction, discord.utils.get(message.reactions, emoji="❌"))
        if event.emoji.name == "❌" and reaction.count > server_conf.minimum_vote:
            await message.edit(
                embed=create_embed(
                    "*This confession has been deleted by vote.*",
                    use_quote=False,
                )
            )
            await confess.delete()
            await self.on_vote_delete(confess)

    async def on_slash_command_error(self, ctx: SlashContext, error: Exception):
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send("You can only use this inside a server.", hidden=True)
        elif isinstance(error, NoConfig):
            return await ctx.send("Server is not configured.", hidden=True)
        elif isinstance(error, Forbidden):
            return await ctx.send("You cannot use this command.", hidden=True)
        else:
            error = getattr(error, "original", error)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            return await ctx.send(
                "An exception has occured: `{}` on command `{}`".format(
                    error.__class__.__name__, ctx.name
                )
            )

    async def on_command_error(self, ctx: Context, error: Exception):
        ignored = (commands.CommandNotFound, commands.CheckFailure)

        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.UserInputError):
            return await ctx.send_help(ctx.command)
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f"Rate limited. Try again in `{error.retry_after}` seconds."
            )
        elif isinstance(error, commands.CommandInvokeError):
            error = getattr(error, "original", error)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            return await ctx.send(
                "An exception has occured: `{}` on command `{}`".format(
                    error.__class__.__name__, ctx.command.name
                )
            )

    async def on_ready(self):
        print("Running!")
        presence = discord.Game(name="/confess")
        await self.change_presence(activity=presence)

    async def start(self, *args, **kwargs):
        if not database.is_connected:
            await database.connect()
        await super().start(*args, **kwargs)

    async def close(self):
        # Cleanup db connection
        if database.is_connected:
            await database.disconnect()
        await super().close()


def run():
    bot = Fess(command_prefix="p!", intents=discord.Intents.default())
    bot.run(config.token)
