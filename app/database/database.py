import pymongo
import logging

logger = logging.getLogger(__name__)


class Database:

    def __init__(self):

        self.database = Database._create_database()
        self.colllection = None

        # create message collection
        self.collection = self.create_collections()

    @staticmethod
    def _create_database():
        try:
            db = pymongo.MongoClient(host="mongo:27017")
            return db
        except Exception as e:
            logger.critical("Could not create database. Error %s", e)
            return None

    def create_collections(self):
        return self.database['messages']
