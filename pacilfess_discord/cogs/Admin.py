from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

from discord import Member, TextChannel
from discord.ext.commands import Cog, check
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_choice, create_option

from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.hasher import decrypt_data, hash_user
from pacilfess_discord.helper.regex import DISCORD_RE
from pacilfess_discord.helper.utils import check_banned, is_admin
from pacilfess_discord.models import Confess, DeletedData, ServerConfig, Violation

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess

severity_option = create_option(
    name="severity",
    description="The severity of the rule violation.",
    option_type=SlashCommandOptionType.INTEGER,
    required=True,
    choices=[
        create_choice(i + 1, x) for i, x in enumerate(["small", "medium", "severe"])
    ],
)


class Admin(Cog):
    def __init__(self, bot: "Fess"):
        self.bot = bot

    async def _delete_fess(self, ctx: SlashContext, link: str) -> Optional[Confess]:
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild_id)
        if not server_conf.confession_channel:
            return await ctx.send(
                "This server has not been configured. Please contact the server admin.",
                hidden=True,
            )

        confession_channel = cast(
            Optional[TextChannel], self.bot.get_channel(server_conf.confession_channel)
        )
        if not confession_channel:
            return await ctx.send(
                "Cannot seem to find confession channel. Maybe it was deleted?",
                hidden=True,
            )

        re_result = DISCORD_RE.search(link)
        if not re_result:
            await ctx.send("Invalid confession link!", hidden=True)
            return None

        confess = await Confess.objects.get_or_none(
            message_id=int(re_result.group("MESSAGE")), server_id=ctx.guild_id
        )

        if not confess:
            await ctx.send(
                "No such confession found.",
                hidden=True,
            )
            return None

        confess_id: int = confess.message_id
        confess_msg = await confession_channel.fetch_message(confess_id)
        await confess_msg.edit(
            embed=create_embed(
                "*This confession has been deleted by admin.*",
                use_quote=False,
            )
        )

        await confess.delete()
        return confess

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="mute",
        description="Temporarily mute/ban a user from message for a specific time.",
        options=[
            create_option(
                name="message",
                description="Link to message in which the user will be banned.",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
            severity_option,
        ],
    )
    @check(is_admin)
    async def _mute(self, ctx: SlashContext, message: str, severity: int):
        current_time = datetime.now()
        confess = await self._delete_fess(ctx, message)
        if not confess:
            await ctx.send("Confess cannot be found, aborting.", hidden=True)
            return

        await Violation.objects.create(
            user_id=confess.user_id,
            server_id=confess.server_id,
            severity=severity,
            timestamp=current_time.timestamp(),
        )
        await self.bot.on_sev_change(confess.user_id, confess.server_id)
        await ctx.send("User has been muted.", hidden=True)

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="muteid",
        description="Temporarily mute/ban a user from ID for a specific time.",
        options=[
            create_option(
                name="id",
                description="The deleted message ID.",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            ),
            severity_option,
        ],
    )
    @check(is_admin)
    async def _muteid(self, ctx: SlashContext, id: str, severity: int):
        current_time = datetime.now()
        try:
            deleted_data = decrypt_data(id, DeletedData)
        except Exception:
            await ctx.send(
                "An error occured, are you sure you're sending the right ID?",
                hidden=True,
            )
            return

        await Violation.objects.create(
            user_id=deleted_data.uid,
            server_id=deleted_data.sid,
            severity=severity,
            timestamp=current_time.timestamp(),
        )
        await self.bot.on_sev_change(deleted_data.uid, deleted_data.sid)
        await ctx.send("User has been muted.", hidden=True)

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="unmute",
        description="Unmutes a user.",
        options=[
            create_option(
                name="user",
                description="User to unmute.",
                option_type=SlashCommandOptionType.USER,
                required=True,
            )
        ],
    )
    @check(is_admin)
    async def _unmute(self, ctx: SlashContext, user: Member):
        existing_ban = await check_banned(hash_user(user), ctx.guild_id)
        if not existing_ban:
            await ctx.send("User is not muted.", hidden=True)
            return

        await existing_ban.delete()
        await ctx.send("User has been unmuted.", hidden=True)

    @cog_ext.cog_subcommand(
        base="fessmin",
        name="delete",
        description="Deletes a confess.",
        options=[
            create_option(
                name="link",
                description="Message link to confess.",
                option_type=SlashCommandOptionType.STRING,
                required=True,
            )
        ],
    )
    @check(is_admin)
    async def _delete(self, ctx: SlashContext, link: str):
        if await self._delete_fess(ctx, link):
            await ctx.send("Done!", hidden=True)


def setup(bot: "Fess"):
    bot.add_cog(Admin(bot))
