import socket
import json
import logging
import pprint
import os
import time

from socket import AF_INET, SOCK_STREAM, AF_INET6

log = logging.getLogger(__name__)


class IRC:

    def __init__(self, queue_in, queue_out, channels=[], server="", nickname=None):
        self.running = False

        # connection
        self.socket = socket.socket(AF_INET, SOCK_STREAM)
        self.port = 6667

        if not server:
            self.address = "irc.nebula.fi"
        else:
            self.address = server

        # queues to comminicate outside of thread
        self.queue_in = queue_in
        self.queue_out = queue_out

        # Bot's credentials
        if nickname:  # bot's nick
            self.nickname = nickname
        else:
            self.nickname = "MultiChannelBot"  # default

        self.bot_name = "MultiChannelBot"  # used for realname and username

        self.commands = self._setup_commands()

        self.channels = channels

    def join_channel(self, channel):
        try:
            self.socket.send("JOIN {}\r\n".format(channel).encode("utf-8"))
        except Exception:
            return False
        return True

    def connect_to_server(self):
        """
        Creates connection to IRC server

        :return: True if connection to server was succesful, otherwise False
        """
        try:
            self.socket.connect((self.address, self.port))
            # login to server
            self.socket.send("USER {} a a {}\r\n".format(self.bot_name, self.bot_name).encode("utf-8"))
            # define nick
            self.socket.send("NICK {}\r\n".format(self.nickname).encode("utf-8"))

            for channel in self.channels:
                self.socket.send("JOIN {}\r\n".format(channel).encode("utf-8"))
                time.sleep(1)

            return True  # connection was succesful
        except Exception as e:
            log.critical("Error during connection. Error %s", e)
            return False

    def _join_channels(self, channels=None):
        if not channels:
            channels = self.channels

        for channel in channels:
            self.socket.send("JOIN {}\r\n".format(channel).encode("utf-8"))
            self.channels.append(channel)

    def _response_to_ping(self, msg):
        """
        Responses to server when ping is asked.

        :param msg: Received message
        """
        self.socket.send("PONG {}\r\n".format(msg).encode('utf-8'))

    def is_running(self):
        """
        Tells if bot is running in instance

        :return: False if bot is not running, otherwise True
        """
        return self.running

    def get_channels(self):
        return self.default_channels

    def send_message(self, users, msg, msg_id=""):
        """
        Sents message to to all selected users.

        :param users: List of users that message should be sent. In case of channel list containing channel name
        :param msg: Message which will be sent
        :return: True if message is sent succesfully otherwise False
        """
        try:
            for user in users:
                if not isinstance(user, str):  # ensure that users are strings
                    user = str(user)
                self.socket.send("PRIVMSG {} :{:}\r\n".format(user, msg).encode('utf-8'))

            if msg_id:
                self._make_queue_entry({"users": users, "message":msg, "message_id": msg_id})

            return True
        except (socket.error, TypeError, AttributeError, ValueError) as e:
            log.critical("Error during senting message. Error: %s", e)
            return False

    def _get_messgae_data(self):
        data = self.socket.recv(4096).decode('utf-8').strip('\r\n')
        return data

    def receive_messages(self):
        """
        Catches messages that are sent to the bot

        :return: received message data
        """
        # TODO check if there is better format for the messages
        # also other response handling probably should be done here
        data = self._get_messgae_data()
        if log.isEnabledFor(logging.DEBUG):
            log.debug("%s", pprint.pformat(data))

        if "PING" in data:
            self._response_to_ping(data)
        else:
            self.handle_incoming_messages(data=data)

    def _determine_if_msg_recived(self, user, timestamp):
        """
        Determines if user has received the message.

        :param users: users that message has been sent
        :return: None if server doesn't support idle, otherwise boolean True if message is seen or False if not seen.
        """
        self.socket.send(("WHOIS {}\r\n").format("vinvin").encode('utf-8'))
        data = self._get_messgae_data()
        if "IDLE" not in data:
            log.warning("Server does not show idle")
            return None

        idle_time = MessageParser.parse_idle_time(data)
        # we need messages timestamp to compare login time and sent time
        if idle_time <= timestamp:
            return True

        return False

    def handle_incoming_messages(self, data, seen=False):
        result_dict = MessageParser.parse_incoming_messages(data, self.commands)
        if not result_dict:
            return None

        command = result_dict.get("command", "")
        if command:
            command(result_dict)


    def handle_response(self, parse_result):
        """
        Inserts parse result to queue and passes it to api
        """
        try:
            return self._make_queue_entry(parse_result)
        except Exception as e:
            log.warning("Error %s in queue", e)
            return None

    def print_help(self, parse_result):
        """
        """
        #result_dict = MessageParser.parse_incoming_messages(message=msg)
        message = "Bot commands are: {}".format(" ".join(self.commands.keys()))
        self.send_message(users=[parse_result.get("channel")], msg=message)

    def _setup_commands(self):
        """
        """
        commands = {
            "!response": self.handle_response,  # handles aswers from user
            "!help": self.print_help
        }
        return commands

    def _make_queue_entry(self, data):
        """
        Adds item to the queue to be added into database.
        """
        try:
            del data['command']  # internal command should not be saved into database
            self.queue_out.put(data)
        except Exception as e:
            log.critical("Data cannot be queued. Error %s", e)
            return False
        return True

    def _get_queue_item(self):
        if self.queue_in.empty():
            return None

        data = self.queue_in.get(timeout=10)
        if data:
            return data
        return None

    def handle_queue(self, data):
        """
        Handles queue and checks what kind of operations needs to be done.

        :param data: A dict containing operation type and needed information
        """
        entry_type = data.get("type")
        if entry_type == "message":
            user = data.get("receiver", "")
            message = data.get("message", "")
            message = "Message id {} {}".format(data.get("_id"), message)

            status = self.send_message(users=user, msg=message, msg_id=data.get("_id"))

            return status
        elif entry_type == "status":
            # do da handling in api
            timestamp = data.get("sent")
            users = data.get("sent_to")
            self._determine_if_msg_recived(user=users, timestamp=timestamp)
        elif entry_type == "stop":
            log.info("Irc bot is shutting down")
            self.running = False


def run_irc(*args, **kwargs):
    """
    Method to run irc bot.
    """
    irc = IRC(queue_in=kwargs.get("queue_in"), queue_out=kwargs.get("queue_out"))
    irc.connect_to_server()
    irc.running = True
    log.info("IRC bot is running")
    while irc.running:
        data = irc._get_queue_item()
        if data:
            irc.handle_queue(data)
        irc.receive_messages()


class MessageParser:
    """
    Parser for incoming and outgoing messages
    """

    @staticmethod
    def parse_incoming_messages(message, commands):
        """
        Parser for messages that are sent to the bot.

        :param message: A list containing message data
        :return: A dict with used channel and message string
        """

        parse_result = {
            "message": "",
            "command": None,
            "channel": MessageParser._get_channel(message=message),
            "user": MessageParser._get_sender(message=message)
        }
        try:
            msg = message.split(':')[-1]
            if not msg:
                return ""

            if not msg.startswith("!"):
                return ""

            msg = msg.split()
            command = commands.get(msg[0])
            if command:
                parse_result['command'] = command
                if command == "!help":
                    return parse_result

            parse_result["message_id"] = msg[1]
            parse_result['message'] = msg[2]

        except (IndexError, TypeError) as e:
            log.warning("Error during message parsing. Error: %s", e)
            return parse_result

        return parse_result

    @staticmethod
    def _get_sender(message):
        try:
            sender = message.split("!")[0].strip(":")
            return sender
        except IndexError:
            return ""

    @staticmethod
    def _get_channel(message):
        try:
            channel = message.split("PRIVMSG")[1].split("!")[0].strip(":").strip()
            if channel.find("MultiChannelBot") == -1:
                return channel
            return MessageParser._get_sender(message=message)
        except (IndexError, TypeError, AttributeError):
            return ""

    @staticmethod
    def parse_idle_time(message):
        return ""
