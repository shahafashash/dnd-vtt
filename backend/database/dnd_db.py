import os
from dotenv import load_dotenv
from backend.database.db import Database


load_dotenv()


class DndDatabase(Database):
    def __init__(self) -> None:
        connection_string = os.getenv("MONGO_CONNECTION_STRING")
        connection_string = connection_string.format(
            username=username, password=password
        )
        database_name = os.getenv("MONGO_DATABASE_NAME")
        super().__init__(connection_string, database_name)
