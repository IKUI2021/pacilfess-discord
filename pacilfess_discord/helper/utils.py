from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from discord_slash.context import SlashContext

from pacilfess_discord.models import BannedUser, ServerConfig


class NoConfig(commands.CheckFailure):
    pass


class Forbidden(commands.CheckFailure):
    pass


async def check_banned(user_id: str, server_id: int):
    current_time = datetime.now()

    existing_ban = await BannedUser.objects.get_or_none(
        user_id=user_id, server_id=server_id
    )
    if existing_ban:
        if current_time < existing_ban.datetime:
            return existing_ban
        else:
            await existing_ban.delete()

    return None


def owner_or_admin():
    original = commands.has_permissions(manage_guild=True).predicate

    async def extended_check(ctx: Context):
        if ctx.guild is None:
            return False
        return ctx.guild.owner_id == ctx.author.id or await original(ctx)

    return commands.check(extended_check)


async def is_admin(ctx: SlashContext):
    if not ctx.guild_id:
        raise commands.NoPrivateMessage()

    server_conf = await ServerConfig.objects.get_or_none(server_id=ctx.guild_id)
    if not server_conf:
        raise NoConfig()

    for role_id in server_conf.admin_roles:
        r = discord.utils.get(ctx.author.roles, id=role_id)
        if r:
            return True

    raise Forbidden()
