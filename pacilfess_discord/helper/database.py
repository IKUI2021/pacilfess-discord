import databases
import sqlalchemy

from pacilfess_discord.config import config

database = databases.Database(config.db_url)
metadata = sqlalchemy.MetaData()
