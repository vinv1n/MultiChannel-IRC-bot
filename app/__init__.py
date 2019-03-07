import logging
import threading
import time
import os
import json

# flask stuffenings
from flask import Flask, render_template
from flask_restful import Api, Resource

# bot handling utility
from queue import Queue
from app.bots.irc_bot import run_irc

from app.database.database import Database

# resources
from app.resources.messages import Messages, SingleMessage, SingleMessageStatus, JoinChannel

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

    db = Database()
    # start irc thread
    bot = BOT_Launch(database=db)
    bot.create_thread()

    # Api resources
    api.add_resource(Messages, "/messages/",
        resource_class_kwargs={"bot": bot, "database": db}
    )
    api.add_resource(SingleMessage, "/messages/<string:id>",
        resource_class_kwargs={"bot": bot}
    )
    api.add_resource(SingleMessageStatus, "/messages/<string:id>/status",
        resource_class_kwargs={"bot": bot}
    )
    api.add_resource(JoinChannel, "/join/<string:channel>",
        resource_class_kwargs={"bot": bot}
    )

    return app


class BOT_Launch:
    """
    Creates instances of channels
    """
    def __init__(self, database):
        self.queue_in = Queue()
        self.queue_out = Queue()

        self.database = database

    def _load_config(self):
        def load_config():
            conf = None
            try:
                with open(os.path.join(os.getcwd(), "config.json"), "r") as config:
                    conf = json.loads(config.read())
            except (IOError, OSError, KeyError):
                return None

            if not conf:
                return {}

            return conf["irc"]

        conf = load_config()

        nick = None
        server = None
        channels = None
        try:
            nick = conf["nickname"]
            server = conf["server"]
            channels = conf["channels"]
        except KeyError:
            return None, None, None

        return nick, channels, server

    def create_thread(self):
        nick, channels, server = self._load_config()

        threading.Thread(target=run_irc, kwargs={"queue_in": self.queue_in, "queue_out": self.queue_out,
                            "channels": channels, "nickname": nick, "server": server}).start()
        threading.Thread(target=self.get_queue_items).start()

    def get_queue_items(self):
        while True:
            if not self.queue_out.empty():
                item = self.queue_out.get()
                logger.info("%s", item)
                success = self.database.add_item(item)
                logger.info("Message %s", success)

            time.sleep(2)

