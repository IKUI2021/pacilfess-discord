from hashlib import sha256
import discord


def hash_user(user: discord.Member):
    return sha256(str(user.id).encode()).hexdigest()
