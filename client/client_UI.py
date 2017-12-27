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
                                          User INFO
---------------------------------------------------------------------------------------------------------------------"""
class Userinfo():
    def __init__(self):
        self.currentname = ''
        self.names = ['Or select your previous names', ]
        self.score = 0
        self.gameid = 0

    """set methods"""

    def setname(self, n):
        self.currentname = n

    def setscore(self, n):
        self.score = n

    """get methods"""

    def getname(self):
        return self.currentname

    def getscore(self):
        return self.score

    def getoldnames(self):
        return self.names

    def getgameid(self):
        return self.gameid


"""---------------------------------------------------------------------------------------------------------------------
                                          Client UI
---------------------------------------------------------------------------------------------------------------------"""
# **Client**---------------------------------------------------------------------------------------------------
class Client(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.title('Sodoku Game Application')
        logging.debug('Client has started!')
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # create user instance
        self.user = Userinfo()
        self.frames = {}
        for F in (Login, ConnectServer, Joining, NewSession, GameSession):
            page_name = F.__name__
            frame = F(master=container, controller=self)  # init page
            self.frames[page_name] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConnectServer")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

    def get_frame(self, page_name):
        return self.frames[page_name]


# **ConnectServer**---------------------------------------------------------------------------------------
class ConnectServer(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'ConnectServer' Frame
        self.consrv_frame = Frame(self, width=350, height=150, pady=75)
        self.consrv_frame.pack()

        # head label
        label = Label(self.consrv_frame, text='Choose your server', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        # server list
        self.srvlist = Listbox(self.consrv_frame, height=10)
        self.srvlist.grid(row=1, column=0, columnspan=2)
        # submit button
        self.submit_button = Button(self.consrv_frame, text='Connnect', command=self.connect)
        self.submit_button.grid(row=2, column=0, sticky=NSEW)
        self.quit_button = Button(self.consrv_frame, text='Quit', command=self.quit)
        self.quit_button.grid(row=2, column=1, sticky=NSEW)
        # bind key
        self.srvlist.bind('<Return>', self.connect)

        # start detect server
        self.server_detect()
        self.update_srv()

        logging.debug('Loading *Connectserver* Page success!')

    def connect(self, e=None):
        return

    def server_detect(self):
        logging.debug('Started server detection!')
        mc_ip, mc_port = '239.1.1.1', 7778
        mc = detect_server(mc_ip, mc_port)
        mc.daemon = True
        mc.start()
        sleep(60)
        mc.stop()
        logging.debug('Stopped server detection!')
        return

    def update_srv(self):
        return