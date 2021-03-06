from Tkinter import *
import tkMessageBox
import tkFont as tkfont
import ttk
import logging
import pika
import uuid
import threading
import time
from detect_server import detect_server
from time import sleep

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(threadName)-2s) %(message)s', )
"""---------------------------------------------------------------------------------------------------------------------
                                             Constants

    i) Server use double headers: Control code+SEP+RSP/NOTI+message
   ii) Client use: REQ+SEP+message
   eg. Client send: REQ_JOIN:1:shan 
       Server reply: CTR_RSP:RSP_OK (no message) 
       Server notify: CTR_NOT:NOTI_JOIN:shan
---------------------------------------------------------------------------------------------------------------------"""
# msg sep
MSG_SEP = ':'
DTA_SEP = '/'
# control code
CTR_NOT = '0'
CTR_RSP = '1'
# server response
RSP_ERR = '0'
RSP_OK = '1'
RSP_DUP = '2'
# client code
REQ_NAME = '0'
REQ_CREATE = '1'
REQ_JOIN = '2'
REQ_MOVE = '3'
REQ_QUIT = '4'  # not on paper!! client send: `Header:gameid:username`
# server reply: `CTR_RSP:RSP_OK` notify others: `CTR_NOT:NOTI_QUIT:name`
REQ_getRoom = '5'
REQ_getSudoku = '6'
REQ_getUser = '7'
# notifications
NOTI_JOIN = '0'
NOTI_MOVE = '1'
NOTI_QUIT = '2'
NOTI_WINNER = '3'

"""---------------------------------------------------------------------------------------------------------------------
                                            User & Notifications
---------------------------------------------------------------------------------------------------------------------"""


class User(object):
    def __init__(self, controller):
        self.name = ''
        self.score = 0
        self.gameid = 0
        self.limit = 0
        self.number = 0
        self.server_q = None
        self.corr_id = None
        # get controller
        self.controller = controller
        # other variables
        self.connection = None
        self.channel = None
        self.queue = None
        self.response = None

    def init_rabbitmq(self):
        # establish connection
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
        # declare channel
        self.channel = self.connection.channel()
        # declare client unique callback queue
        self.queue = str(uuid.uuid4())
        self.channel.queue_declare(queue=self.queue, exclusive=True)
        # self.channel.basic_qos(prefetch_count=1)
        # listening on self queue
        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.queue)
        t = threading.Thread(target=self.start_consume)
        t.start()

    def on_response(self, ch, method, props, body):
        # if notification
        if body.startswith(CTR_NOT + MSG_SEP):
            # do notification
            msg = body[2:]
            if msg.startswith(NOTI_JOIN + MSG_SEP):
                self.number += 1
                frame = self.controller.frames['Gamesession']
                frame.update_user()
                if self.number == self.limit:
                    frame.start_game()
            elif msg.startswith(NOTI_MOVE + MSG_SEP):
                pass
            elif msg.startswith(NOTI_QUIT + MSG_SEP):
                pass
            elif msg.startswith(NOTI_WINNER + MSG_SEP):
                msg = msg[2:]
                next_msg = msg.find(MSG_SEP)
                self.username = msg[2:next_msg]
                self.score = msg[next_msg+1:]
        # if response
        elif body.startswith(CTR_RSP + MSG_SEP):
            body = body[2:]
            if self.corr_id == props.correlation_id:
                self.response = body
        return

    def call(self, req, m):
        # compose msg
        msg = req + MSG_SEP + str(m)
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.server_q,
                                   properties=pika.BasicProperties(
                                       reply_to=self.queue,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=msg)
        while self.response is None:
            # self.connection.process_data_events()
            pass
        rsp = self.response
        self.response = None
        return rsp

    def start_consume(self):
        self.channel.start_consuming()
        return

    def __repr__(self):
        return 'User(name=%s, gameid=%s, score=%s, server_q=%s)' % (
            self.name, self.gameid, self.score, self.server_q)
