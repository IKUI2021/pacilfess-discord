import aiosqlite
import discord
from typing import cast
from discord.channel import TextChannel
from discord.ext.commands import Bot
from discord.raw_models import RawReactionActionEvent
from discord.reaction import Reaction
from discord_slash import SlashCommand

from pacilfess_discord.helper.embed import create_embed
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

    async def on_raw_reaction_add(self, event: RawReactionActionEvent):
        confess = await self.db.fetchone(
            "SELECT * FROM confessions WHERE message_id=?",
            (event.message_id,),
        )
        if not confess:
            return

        message = await self.target_channel.fetch_message(event.message_id)

        # OK I legit don't know why is Reaction.emoji here is an str but on the event object,
        # its a PartialEmoji, kinda makes it a huge pain in the ass to be honest.
        reaction = cast(Reaction, discord.utils.get(message.reactions, emoji="❌"))
        if (
            event.emoji.name == "❌" and reaction.count > config.minimum_vote + 1
        ):  # +1 because bot also counts
            await message.edit(
                embed=create_embed("*This confession has been deleted by vote.*")
            )
            await self.db.execute(
                "DELETE FROM confessions WHERE message_id=?",
                (event.message_id,),
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
