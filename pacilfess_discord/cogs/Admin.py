from typing import TYPE_CHECKING, cast, Match

from datetime import datetime, timedelta
from discord import Member

from discord.ext.commands import Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.config import config
from pacilfess_discord.helper.regex import DISCORD_RE, ETA_RE

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess


class Admin(Cog):
    def __init__(self, bot: "Fess"):
        self.bot = bot

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="mute",
        description="Temporarily mute/ban a user for a specific time.",
        guild_ids=[config.guild_id],
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

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="unmute",
        description="Unmutes a user.",
        guild_ids=[config.guild_id],
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

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="delete",
        description="Deletes a confess.",
        guild_ids=[config.guild_id],
        options=[
            create_option(
                name="link",
                description="Message link to confess.",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            )
        ],
    )
    async def _delete(self, ctx: SlashContext, link: str):
        re_result = DISCORD_RE.search(link)
        if not re_result:
            await ctx.send("Invalid confession link!", hidden=True)
            return

        confess = await self.bot.db.fetchone(
            "SELECT * FROM confessions WHERE message_id=?",
            (int(re_result.group("MESSAGE")),),
        )

        if not confess:
            await ctx.send(
                "No such confession found.",
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


def setup(bot: "Fess"):
    bot.add_cog(Admin(bot))
