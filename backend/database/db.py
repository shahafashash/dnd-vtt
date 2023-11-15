from typing import Dict, List, Any
import pymongo
import certifi


class Database:
    def __init__(self, connection_string: str, database_name: str) -> None:
        self.__connection_string = connection_string
        self.__database_name = database_name
        self.__con = None
        self.__database = None

    @property
    def connection_string(self) -> str:
        return self.__connection_string

    @property
    def database_name(self) -> str:
        return self.__database_name

    def __enter__(self) -> "Database":
        self.__create_connection()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.__con is not None:
            self.__con.close()
            self.__con = None

    def __create_connection(self) -> pymongo.database.Database:
        try:
            self.__con = pymongo.MongoClient(
                self.__connection_string, connect=True, tlsCAFile=certifi.where()
            )
        except pymongo.errors.ConnectionFailure as e:
            print(f"Could not connect to server: {e}")
            return None

        self.__database = self.__con.get_database(self.__database_name)
        return self.__database

    def create_collection(
        self, collection_name: str, data: Dict[str, Any] | List[Dict[str, Any]]
    ) -> None:
        self.insert(collection_name, data)

    def drop_collection(self, collection_name: str) -> None:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        collection.drop()

    def insert(
        self, collection_name: str, data: Dict[str, Any] | List[Dict[str, Any]]
    ) -> None:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        if isinstance(data, list):
            collection.insert_many(data)
        else:
            collection.insert_one(data)

    def delete(self, collection_name: str, query: Dict[str, Any]) -> None:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        collection.delete_one(query)

    def find(
        self, collection_name: str, query: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)

        if query is None:
            query = {}

        return list(collection.find(query))

    def find_one(
        self, collection_name: str, query: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        if query is None:
            query = {}

        return collection.find_one(query)

    def find_all(self, collection_name: str) -> List[Dict[str, Any]]:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        return list(collection.find({}))

    def update(
        self, collection_name: str, query: Dict[str, Any], data: Dict[str, Any]
    ) -> None:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        collection.update_one(query, {"$set": data})

    def list_collection_names(self) -> List[str]:
        if self.__con is None:
            self.__create_connection()

        return self.__database.list_collection_names()

    def create_index(
        self,
        collection_name: str,
        index: str,
        index_type: int = pymongo.ASCENDING,
        unique: bool = False,
    ) -> None:
        if self.__con is None:
            self.__create_connection()

        collection = self.__database.get_collection(collection_name)
        collection.create_index([(index, index_type)], unique=unique)
