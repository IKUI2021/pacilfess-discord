import random
from base64 import b64decode, b64encode
from hashlib import sha256
from typing import Type, cast

import discord
from Crypto.Cipher import Salsa20
from Crypto.Protocol.KDF import scrypt
from dataclasses_json.api import DataClassJsonMixin

from pacilfess_discord.config import config

random.seed("pacilfess-dc")
salt = random.randbytes(32)
key = cast(bytes, scrypt(config.secret, salt, 16, N=2 ** 14, r=8, p=1))  # type: ignore


def hash_user(user: discord.Member):
    return sha256(str(user.id).encode()).hexdigest()


def enc_data(obj: DataClassJsonMixin):
    cipher = Salsa20.new(key)
    encrypted_data = cipher.encrypt(obj.to_json().encode())
    assert isinstance(encrypted_data, bytes)

    output_data = cipher.nonce + encrypted_data
    return b64encode(bytes(output_data))


def decrypt_data(enc: str, cls: Type[DataClassJsonMixin]):
    decoded_data = b64decode(enc)

    cipher = Salsa20.new(key, nonce=decoded_data[:8])
    output = cipher.decrypt(decoded_data[8:])
    return cls.from_json(output)
