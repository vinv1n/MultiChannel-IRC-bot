"""
This is really simple implementation of API for IRC bot.
This have to make it's own database to handle stuff
"""

import logging
import threading
import base64

# flask stuffenings
from flask import Flask, render_template
from flask_restful import Api, Resource

from queue import Queue
from app.irc_bot import run_irc


def create_api():

    app = Flask(__name__)
    app.config.from_object("config")

    api = Api(app)

    # Api resources
    api.add_resource(Messages, "/messages/<string:data>")
    api.add_resource(SingleMessage, "/messages/<int:id>")
    api.add_resource(SingleMessageStatus, "/messages/<int:id>/status")

    # start irc thread
    bot = BOT_Launch()
    bot.create_thread()
    print("is running")
    return app


class Messages(Resource):
    """
    Send message, data as base64 encoded json
    """

    def post(self, data):
        pass


class SingleMessage(Resource):

    def get(self, id):
        pass


class SingleMessageStatus(Resource):
    """
    Get one sent message
    """
    def get(self, id):
        pass


class BOT_Launch:
    """
    Creates instances of channels
    """
    def __init__(self):
        self.queue_in_irc = Queue()
        self.queue_out_irc = Queue()

    def create_thread(self):
        # FIXME this is horrible solution
        threading.Thread(target=run_irc, kwargs={"queue_in": self.queue_in_irc,
                            "queue_out": self.queue_out_irc}).start()
