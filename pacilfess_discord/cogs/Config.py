from typing import TYPE_CHECKING

from discord.channel import TextChannel
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import guild_only
from discord.guild import Guild
from discord.role import Role

from pacilfess_discord.helper.utils import owner_or_admin
from pacilfess_discord.models import ServerConfig

if TYPE_CHECKING:
    from pacilfess_discord.bot import Fess


class Config(commands.Cog):
    def __init__(self, bot: "Fess"):
        self.bot = bot

    @commands.command(help="Sets where the confessions are going to be sent.")
    @guild_only()
    @owner_or_admin()
    async def fess_channel(self, ctx: Context, channel: TextChannel):
        assert isinstance(ctx.guild, Guild)
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild.id)
        server_conf.confession_channel = channel.id
        await server_conf.update()
        await ctx.send(f"Done setting confession channel to {channel.mention}.")

    @commands.command(
        help="Sets where the vote deleted messages are going to be logged."
    )
    @guild_only()
    @owner_or_admin()
    async def votelog_channel(self, ctx: Context, channel: TextChannel):
        assert isinstance(ctx.guild, Guild)
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild.id)
        server_conf.votelog_channel = channel.id
        await server_conf.update()
        await ctx.send(f"Done setting vote logging channel to {channel.mention}.")

    @commands.command(help="Adds a role to the list of bot admins.")
    @guild_only()
    @owner_or_admin()
    async def add_admin(self, ctx: Context, role: Role):
        assert isinstance(ctx.guild, Guild)
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild.id)
        server_conf.admin_roles.append(role.id)
        await server_conf.update()
        await ctx.send(f"Done adding {Role.mention} to admins.")

    @commands.command(help="Override the minimum vote required for vote deletion.")
    @guild_only()
    @owner_or_admin()
    async def minimum_vote(self, ctx: Context, minimum: int):
        assert isinstance(ctx.guild, Guild)
        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild.id)
        server_conf.minimum_vote = minimum
        await server_conf.update()
        await ctx.send(f"Done setting minimum vote deletion to {minimum}.")

    @commands.command(help="List all of the configuration.")
    @guild_only()
    @owner_or_admin()
    async def list(self, ctx: Context):
        assert isinstance(ctx.guild, Guild)

        server_conf = await ServerConfig.objects.get_or_create(server_id=ctx.guild.id)

        channel_str = "None"
        if server_conf.confession_channel:
            chl = ctx.guild.get_channel(server_conf.confession_channel)
            if chl:
                channel_str = chl.mention

        votelog_str = "None"
        if server_conf.votelog_channel:
            chl = ctx.guild.get_channel(server_conf.votelog_channel)
            if chl:
                votelog_str = chl.mention

        admins_str = "None"
        if server_conf.admin_roles:
            s = []
            for role in server_conf.admin_roles:
                r = ctx.guild.get_role(role)
                if r:
                    s.append(r.mention)

            if s:
                admins_str = ", ".join(s)

        conf_str = (
            "Server configuration:"
            + "\r\nFess channel: "
            + channel_str
            + "\r\nVote log channel: "
            + votelog_str
            + "\r\nAdmins: "
            + admins_str
            + "\r\nMinimum vote for deletion: "
            + str(server_conf.minimum_vote)
        )
        await ctx.send(conf_str)


def setup(bot: "Fess"):
    bot.add_cog(Config(bot))