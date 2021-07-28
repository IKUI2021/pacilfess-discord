import json

import aiosqlite
import discord
from discord.channel import TextChannel
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from pacilfess_discord.typing import ConfigType

with open("config.json", "r") as f:
    config: ConfigType = json.load(f)


class Fess(Bot):
    async def on_ready(self):
        print("Running!")
        self.target_channel: TextChannel = self.get_channel(config["channel_id"])
        presence = discord.Game(name="/confess")
        await self.change_presence(activity=presence)

    async def start(self, *args, **kwargs):
        # Can't really think of a better to place to connect, so I'm placing it right after
        # run() execution, should be fine.
        self.db = await aiosqlite.connect(config["db_path"])
        await super().start(*args, **kwargs)

    async def close(self):
        # Cleanup db connection
        await self.db.close()
        await super().close()


bot = Fess(command_prefix="p!", intents=discord.Intents.default())
slash = SlashCommand(bot, sync_commands=True)
for cog in config["cogs"]:
    try:
        bot.load_extension(cog)
    except Exception as exc:
        print(
            "Could not load extension {0} due to {1.__class__.__name__}: {1}".format(
                cog, exc
            )
        )


def run():
    bot.run(config["token"])
