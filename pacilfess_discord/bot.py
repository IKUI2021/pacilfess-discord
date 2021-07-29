import aiosqlite
import discord
from discord.channel import TextChannel
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from pacilfess_discord.helper.db import DBHelper
from pacilfess_discord.config import config


cogs = [
    "pacilfess_discord.cogs.Fess",
    "pacilfess_discord.cogs.Admin",
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

    async def on_ready(self):
        print("Running!")
        self.target_channel: TextChannel = self.get_channel(config.channel_id)
        presence = discord.Game(name="/confess")
        await self.change_presence(activity=presence)

    async def start(self, *args, **kwargs):
        # Can't really think of a better to place to connect, so I'm placing it right after
        # run() execution, should be fine.
        self.db = DBHelper(await aiosqlite.connect(config.db_path))
        await super().start(*args, **kwargs)

    async def close(self):
        # Cleanup db connection
        await self.db.close()
        await super().close()


def run():
    bot = Fess(command_prefix="p!", intents=discord.Intents.default())
    bot.run(config.token)
