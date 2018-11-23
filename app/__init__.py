"""
This is really simple implementation of API for IRC bot.
This have to make it's own database to handle stuff
"""

import logging
import threading

# flask stuffenings
from flask import Flask, render_template
from flask_restful import Api, Resource

# bot handling utility
from queue import Queue
from app.bots.irc_bot import run_irc

# resources
from app.resources.messages import Messages, SingleMessage, SingleMessageStatus

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)-15s:%(name)-s:%(levelname)s %(message)s', datefmt="%a, %d %b %Y %H:%M:%S")
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

logger.addHandler(handler)



logger = logging.getLogger(__name__)

def create_api():

    app = Flask(__name__)
    app.config.from_object("config")

    api = Api(app)

    # start irc thread
    bot = BOT_Launch()
    bot.create_thread()

    # Api resources
    api.add_resource(Messages, "/messages/<string:data>",
        resource_class_kwargs={"bot": bot}
    )
    api.add_resource(SingleMessage, "/messages/<int:id>",
        resource_class_kwargs={"bot": bot}
    )
    api.add_resource(SingleMessageStatus, "/messages/<int:id>/status",
        resource_class_kwargs={"bot": bot}
    )

    return app


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
