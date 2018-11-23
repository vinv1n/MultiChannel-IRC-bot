import base64
import json
import logging

from flask_restful import Resource
from flask import request

logger = logging.getLogger(__name__)

class Messages(Resource):
    """
    Send message, data as base64 encoded json
    or regular json.
    """

    def __init__(self, bot):
        self.bot = bot

    def post(self):
        data = request.get_json()
        if not data:
            return {"error": "no data received"}, 400

        data = decode_message(data)
        if not data:
            return {"error": "Incorrect data format"}, 400

        # TODO add more methods to validate data
        self.bot.queue_in.put_(data)

        # TODO somepoint we probably need to add these to database and make own handler

        return {"success": True}, 200


class SingleMessage(Resource):

    def __init__(self, bot):
        self.bot = bot

    def get(self, id):
        # disabled for now
        pass


class SingleMessageStatus(Resource):
    """
    Get one sent message
    """

    def __init__(self, bot):
        self.bot = bot

    def get(self, msg_id):
        # launches action to check if user is seen message
        # could also be cron job
        # TODO could be implemented after database is added
        pass


def decode_message(data):

    if isinstance(data, dict):
        return data

    try:
        # json could me send as base64 encoded string
        data = base64.b64decode(data)
        return data
    except Exception as e:
        logger.debug("Incorrect message type. Error %s", e)
        return None