# Pacilfess (Discord)

# Information

While I try to make this as general as possible, some things might be a bit technical.

## What is this?

Pacilfess is a Discord bot that sends a confession (or actually--message) anonymously to a channel. That is all.

## How does it work?

It works with Discord's slash command! `/confess` is how you use it. Do not worry, all your interaction with the bot will not be seen by anyone, and nobody can see you typing the commands on the server. After you send that command, it will then send your message to the defined channel.

### Commands

Parameters surrounded with `<>` are required, while those surrounded with `[]` are optional.

-   `/confess <message> [attachment]`: Sends a message anonymously. (optionally, with attachment)  
    **Attachment must be a URL to an image file.**
-   `/delete [message]`: Removes the last fess message you owned. If `message` is supplied with the fess' message URL, then that fess will be deleted instead of the last one.  
    **Only messages earlier than 5 minutes can be removed.** Else, you might want to contact the bot's admin or moderator.
-   `/fessmin`: Admin commands.
    -   `delete <link>`: Removes the linked fess message. This does **NOT** mute the user.
    -   `mute <message> <severity>`: Removes the linked fess message, strikes the user with the specified severity, and mutes the user.
    -   `muteid <id> <severity>`: Mutes the user from the identifier with the specified severity.
    -   `unmute <user>`: Unmutes the user.

## Is this truly anonymous?

Yes! for the most part. Due to the need of moderation, some part of your info is stored in the database, though your plain details is not stored here, only your Discord user ID's hash. You can look it in [pacilfess_discord/models.py](https://github.com/Ilmu-Komputer-UI-2021/pacilfess-discord/blob/main/pacilfess_discord/models.py) file.

---

## How it ACTUALLY works

_This section is technical._

### Fess sending

When a user sends a fess command, it will first check if the user is muted or not. If not, then we will insert the following to the database after we send the message to the predefined channel:

-   Message content
-   Attachment
-   Sender's hashed UID
-   Timestamp
-   Message ID of the SENT channel (not the command)

The message is then reacted with an :x: for the use of vote deletion.

### Fess deletion

Despite the source of deltion, the deletion routine will always FULLY remove your message entry from the database and channel.

#### By owner

If you are an owner of a fess message, you may run a delete command.

#### By admin

If you are an admin, you may run a delete command with the message's url as parameter. However this will _NOT_ punish the user. If you want to punish the user, use mute and link the message's url as parameter.

#### By vote deletion

When a fess is send to the channel, the bot will react with :x: to initiate vote deletion. If the vote count is above the threshold set in config, it will delete the message and LOG it to a channel (if defined in config). The logged datas are the following:

-   The message's content in plain text.
-   The sender's hashed UID and message ID encrypted. [See how it is being encrypted below](#encryption).

### Muted user

A user can be muted due to breaking the rules. It can only be done by the admin, this can be achieved by a few methods:

-   By mentioning the user
-   By giving the message's url as parameter  
    This will also trigger the message deletion routine.
-   By giving the logged data unique identifier  
    This function requires the vote deletion logging to be enabled.

A user will be striked depends on the severity, and is logged to the database. Whenever a mute routine is triggered, the bot will calculate the time of cooldown in the following order:

-   Count all the severity in the last 3 months
-   The cooldown time will be `severityTotal^2 / 2` hours.

## Severity

When a user is striked with a mute command, there will be three options of severity: `small`, `medium`, and `severe`. Each value is `1, 2, 3` respectively. This unit will be determine how long a user will be muted, or should the user be permanently muted from the fess bot.

## Encryption

During vote deletion logging, the user's hashed UID and message ID will be encrypted with Salsa20 and then base64encoded. This is to ensure that whenever a vote delete event occur, the mods wouldn't know who actually sends the message, as the identifier will always change with each message.

To decrypt, we simply do the reverse. Base64 decode, then decrypt with Salsa20.

---

# Developing

## Installing

-   Install [Poetry](https://python-poetry.org/).
-   Run `poetry install`.
-   Create a new `config.json` file with the following format.

```json
{
    "db_path": "data.db",
    "admins": [],
    "admin_roles": [],
    "channel_id": 00000000000000,
    "guild_id": 00000000000000,
    "minimum_vote": 5,
    "token": "",
    "log_channel_id": 00000000000000
}
```

-   Fill in `admins` with list of Discord user IDs, and `channel_id` with the target channel ID.
-   Create an empty file, and run `database.sql` to that database.

## Running

-   Run `poetry run run.py`.

## TODO

-   Add checks on `/fessmin`
