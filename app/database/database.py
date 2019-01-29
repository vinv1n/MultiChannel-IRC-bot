import pymongo
import logging
import json
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class Database:
    # TODO add checks to which message user responses
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
        return self.database['irc_messages']

    def add_item(self, item):
        """
        Adds item to database
        for now this is enough
        """
        data = json.loads(item)
        if not isinstance(data, dict):
            return False

        self.collection.insert_one(item)
        return True

    def get_message(self, message_id):
        """Get a message from database with given ID.

        :param string message_id: the ID of the message.
        :return: the message data as a dictionary."""

        try:
            cursor =  self.database.message_collection.find({'message_id': ObjectId(message_id)})
            message = {}
            for item in cursor:
                for key in item:
                    if key == "_id":
                        message.update({ key : str(item[key]) })
                    else:
                        message.update({ key : item[key] })
            return message
        except Exception as e:
            logger.critical("Error during data handling. Error: %s", e)
            return None

