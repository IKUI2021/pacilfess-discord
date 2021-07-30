from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Match, cast, Optional

from discord import Member
from discord.ext.commands import Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, generate_permissions

from pacilfess_discord.config import config
from pacilfess_discord.helper.hasher import hash_user
from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.regex import DISCORD_RE, ETA_RE
from pacilfess_discord.models import Confess, BannedUser

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess

command_permissions = generate_permissions(
    allowed_roles=config.admin_roles,
    allowed_users=config.admins,
)


class Admin(Cog):
    def __init__(self, bot: "Fess"):
        self.bot = bot

    async def _delete_fess(self, ctx: SlashContext, link: str) -> Optional[Confess]:
        re_result = DISCORD_RE.search(link)
        if not re_result:
            await ctx.send("Invalid confession link!", hidden=True)
            return None

        confess = await self.bot.db.fetchone(
            Confess,
            "SELECT * FROM confessions WHERE message_id=?",
            parameters=(int(re_result.group("MESSAGE")),),
        )

        if not confess:
            await ctx.send(
                "No such confession found.",
                hidden=True,
            )
            return None

        confess_id: int = confess.message_id
        confess_msg = await self.bot.target_channel.fetch_message(confess_id)
        await confess_msg.edit(
            embed=create_embed("*This confession has been deleted by admin.*")
        )

        await self.bot.db.execute(
            "DELETE FROM confessions WHERE message_id=?",
            parameters=(confess_id,),
        )
        return confess

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="mute",
        description="Temporarily mute/ban a user for a specific time.",
        guild_ids=[config.guild_id],
        options=[
            create_option(
                name="message",
                description="Link to message in which the user will be banned.",
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
        base_default_permission=False,
        base_permissions={config.guild_id: command_permissions},
    )
    async def _mute(self, ctx: SlashContext, message: str, time: str):
        eta_re = cast(Match[str], ETA_RE.match(time))
        if not any(eta_re.groups()):
            await ctx.send("Invalid time format.", hidden=True)
            return

        confess = await self._delete_fess(ctx, message)
        if not confess:
            return

        existing_ban = await self.bot.db.fetchone(
            BannedUser,
            "SELECT * FROM banned_users WHERE id=?",
            parameters=(confess.author,),
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
            parameters=(confess.author, lift_datetime.timestamp()),
        )

        await ctx.send(
            f"User has been muted until `{lift_datetime.isoformat(' ', 'seconds')}`.",
            hidden=True,
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
            BannedUser,
            "SELECT * FROM banned_users WHERE id=?",
            parameters=(hash_user(user),),
        )

        if not existing_ban:
            await ctx.send("User is not muted.", hidden=True)
            return

        await self.bot.db.execute(
            "DELETE FROM banned_users WHERE id=?",
            parameters=(hash_user(user),),
        )
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
        if await self._delete_fess(ctx, link):
            await ctx.send("Done!", hidden=True)


def setup(bot: "Fess"):
    bot.add_cog(Admin(bot))
