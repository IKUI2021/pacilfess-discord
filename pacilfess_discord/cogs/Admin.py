from typing import TYPE_CHECKING, cast, Match
import re

from datetime import datetime, timedelta
from discord import Member

from discord.ext.commands import Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from pacilfess_discord.helper.embed import create_embed

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess

ETA_RE = re.compile(
    r"(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?"
)


class Admin(Cog):
    def __init__(self, bot: "Fess"):
        self.bot = bot

    @cog_ext.cog_slash(
        name="fessmute",
        description="Temporarily mute/ban a user for a specific time.",
        guild_ids=[863499218449858570],
        options=[
            create_option(
                name="user",
                description="User to mute.",
                option_type=SlashCommandOptionType.USER,
                required=True,
            ),
            create_option(
                name="time",
                description="The cooldown time.",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
        ],
    )
    async def _mute(self, ctx: SlashContext, user: Member, time: str):
        eta_re = cast(Match[str], ETA_RE.match(time))
        if not any(eta_re.groups()):
            await ctx.send("Invalid time format.", hidden=True)
            return

        existing_ban = await self.bot.db.fetchone(
            "SELECT * FROM banned_users WHERE id=?",
            (user.id,),
        )

        if existing_ban:
            await ctx.send("User is already muted.", hidden=True)
            return

        eta = eta_re.groupdict()
        days = int(eta["days"] or "0")
        hours = int(eta["hours"] or "0")
        minutes = int(eta["minutes"] or "0")
        seconds = int(eta["seconds"] or "0")

        delta = timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours)
        lift_datetime = datetime.now() + delta

        await self.bot.db.execute(
            "INSERT INTO banned_users VALUES (?, ?, ?)",
            (user.id, user.name, lift_datetime.timestamp()),
        )

        await ctx.send(
            f"User has been muted until `{lift_datetime.isoformat(' ')}`.", hidden=True
        )

    @cog_ext.cog_slash(
        name="fessunmute",
        description="Unmutes a user.",
        guild_ids=[863499218449858570],
        options=[
            create_option(
                name="user",
                description="User to unmute.",
                option_type=SlashCommandOptionType.USER,
                required=True,
            )
        ],
    )
    async def _unmute(self, ctx: SlashContext, user: Member):
        existing_ban = await self.bot.db.fetchone(
            "SELECT * FROM banned_users WHERE id=?",
            (user.id,),
        )

        if not existing_ban:
            await ctx.send("User is not muted.", hidden=True)
            return

        await self.bot.db.execute("DELETE FROM banned_users WHERE id=?", (user.id,))
        await ctx.send("User has been unmuted.", hidden=True)


def setup(bot: "Fess"):
    bot.add_cog(Admin(bot))
