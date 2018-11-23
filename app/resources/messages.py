import base64
import json
import logging

from flask_restful import Resource

logger = logging.getLogger(__name__)

class Messages(Resource):
    """
    Send message, data as base64 encoded json
    or regular json.
    """

    def __init__(self, bot):
        self.bot = bot

    def post(self, data):
        if not data:
            return {"error": "no data received"}, 400

        data_json = None
        try:
            data_json = json.loads(base64.b64decode(s=data))
        except (ValueError, AttributeError) as e:
            logger.debug("Error in decoding %s", e)
            data_json = json.loads(data)

        if not data_json:
            return {"error": "Data in incorrect format"}, 400

        # TODO add more methods to validate data
        self.bot.irc_queue_in.put(data)

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

    def get(self, id):
        # launches action to check if user is seen message
        # could also be cron job
        # TODO could be implemented after database is added
        pass

