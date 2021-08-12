from datetime import datetime

from discord.ext import commands
from discord.ext.commands.context import Context

from pacilfess_discord.models import BannedUser


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
