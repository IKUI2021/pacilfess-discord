from datetime import datetime, timedelta
from typing import Optional, Union, cast

import aiosqlite
import discord
from discord.channel import TextChannel
from discord.ext.commands import Bot
from discord.raw_models import RawReactionActionEvent
from discord.reaction import Reaction
from discord_slash import SlashCommand

from pacilfess_discord.config import config
from pacilfess_discord.helper.db import DBHelper
from pacilfess_discord.helper.embed import create_embed
from pacilfess_discord.helper.hasher import enc_data, hash_user
from pacilfess_discord.models import Confess, DeletedData, Violation

cogs = [
    "pacilfess_discord.cogs.Fess",
    "pacilfess_discord.cogs.Admin",
]


class Fess(Bot):
    log_channel: Optional[TextChannel] = None

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

    async def on_vote_delete(self, confess: Confess):
        if not self.log_channel:
            return

        deleted_data = DeletedData(uid=confess.author, mid=confess.message_id)
        encrypted = enc_data(deleted_data)
        embed = create_embed(
            confess.content + f"\r\n\r\nID: `${encrypted.decode('UTF-8')}`",
            attachment=confess.attachment,
            footer="To ban this user, use /fessmin muteid <ID>",
        )
        await self.log_channel.send("Confession deleted from vote:", embed=embed)

    async def on_sev_change(self, user: Union[discord.Member, str]):
        current_time = datetime.now()
        month_ago = current_time - timedelta(weeks=4)

        if isinstance(user, str):
            user_hash = user
        else:
            user_hash = hash_user(user)

        # Remove existing ban just to be safe.
        existing_ban = await self.db.check_banned(user_hash)
        if existing_ban:
            await self.db.execute(
                "DELETE FROM banned_users WHERE id=?",
                parameters=(user_hash,),
            )

        violations = await self.db.fetchall(
            Violation,
            "SELECT * FROM violations WHERE user_hash=? AND timestamp>=?",
            parameters=(user_hash, month_ago.timestamp()),
        )
        total_violations = sum([x.severity for x in violations])
        minutes = total_violations ** 2 * 30

        end_dt = current_time + timedelta(minutes=minutes)
        await self.db.execute(
            "INSERT INTO banned_users(id, timeout) VALUES (?, ?)",
            parameters=(user_hash, end_dt.timestamp()),
        )

    async def on_raw_reaction_add(self, event: RawReactionActionEvent):
        confess = await self.db.fetchone(
            Confess,
            "SELECT * FROM confessions WHERE message_id=?",
            parameters=(event.message_id,),
        )
        if not confess:
            return

        message = await self.target_channel.fetch_message(event.message_id)

        # OK I legit don't know why is Reaction.emoji here is an str but on the event object,
        # its a PartialEmoji, kinda makes it a huge pain in the ass to be honest.
        reaction = cast(Reaction, discord.utils.get(message.reactions, emoji="❌"))
        if event.emoji.name == "❌" and reaction.count > config.minimum_vote:
            await message.edit(
                embed=create_embed("*This confession has been deleted by vote.*")
            )
            await self.db.execute(
                "DELETE FROM confessions WHERE message_id=?",
                parameters=(event.message_id,),
            )
            await self.on_vote_delete(confess)

    async def on_ready(self):
        print("Running!")
        self.target_channel: TextChannel = self.get_channel(config.channel_id)
        if config.log_channel_id:
            self.log_channel = self.get_channel(config.log_channel_id)

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
