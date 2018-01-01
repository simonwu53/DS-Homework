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
from user import User
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
RSP_LATE = '3'
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
        # create user
        self.user = User(self)
        self.user.init_rabbitmq()

        # store client UI frames
        self.frames = {}
        for F in (ConnectServer, Lobby, Newroom, Gamesession):
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
        self.consrv_frame = Frame(self, width=350, height=150, pady=50)
        self.consrv_frame.pack()
        # some variables
        self.mc = None
        self.serverlist = None

        # head label
        label = Label(self.consrv_frame, text='Choose your server', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        # server list
        self.srvlist = Listbox(self.consrv_frame, height=10)
        self.srvlist.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        # enter user name label
        self.name_label = Label(self.consrv_frame, text='Enter your name: ')
        self.name_label.grid(row=2, column=0, sticky=NSEW)
        self.name_entry = Entry(self.consrv_frame)
        self.name_entry.grid(row=2, column=1, sticky=NSEW)
        # submit button
        self.submit_button = Button(self.consrv_frame, text='Connnect', command=self.connect)
        self.submit_button.grid(row=3, column=0, sticky=NSEW)
        self.quit_button = Button(self.consrv_frame, text='Quit', command=self.quit_client)
        self.quit_button.grid(row=3, column=1, sticky=NSEW)
        # bind key
        self.srvlist.bind('<Return>', self.connect)

        # start detect server
        self.server_detect()
        self.update_srv()

        logging.debug('Loading *Connectserver* Page success!')

    def connect(self, e=None):
        # get user selection
        q = [self.srvlist.get(idx) for idx in self.srvlist.curselection()]
        if not q:
            tkMessageBox.showwarning('Error occurred', 'Please select a server first!')
            return
        q = q[0]
        # set server's queue
        self.controller.user.server_q = q
        # get user name
        name = self.name_entry.get()
        # check username
        if not name:
            tkMessageBox.showwarning('Error occurred', 'Please enter your name!')
            return
        rsp = self.controller.user.call(REQ_NAME, name)
        if rsp == RSP_OK:
            logging.debug('User name valid!')
            # set user name
            self.controller.user.name = name
            # update next frame
            frame = self.controller.frames['Lobby']
            frame.prepare()
            # show next frame
            self.controller.show_frame("Lobby")
        elif rsp == RSP_DUP:
            logging.debug('Duplicated username!')
            tkMessageBox.showwarning('Error occurred', 'Your username already exists!')
            self.name_entry.delete(0, END)
            self.name_entry.focus()
        else:
            logging.debug('Unknown Error!')
            tkMessageBox.showwarning('Error occurred', 'Can''t login right now, please try again later!')
            self.name_entry.delete(0, END)
            self.name_entry.focus()
        # stop detect server
        # self.close_detection()
        # connect queue
        logging.debug('User has selected server: %s' % q)
        logging.debug('User set username: %s' % name)
        return

    def server_detect(self):
        logging.debug('Started server detection!')
        mc_ip, mc_port = '239.1.1.1', 7778
        self.mc = detect_server(mc_ip, mc_port)
        self.mc.daemon = True
        self.mc.start()
        return

    def close_detection(self):
        self.mc.stop()
        logging.debug('Stopped server detection!')
        return

    def update_srv(self):
        # clear list box
        self.srvlist.delete(0, END)
        # get server list
        self.serverlist = self.mc.getlist()
        # update GUI
        for server in self.serverlist:
            self.srvlist.insert(END, server)
        # update list regularly
        self.srvlist.after(5000, self.update_srv)
        return

    def prepare(self):
        self.server_detect()
        return

    def quit_client(self):
        self.controller.user.connection.close()
        self.quit()


# **Lobby**---------------------------------------------------------------------------------------
class Lobby(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'Lobby' Frame
        self.lobby_frame = Frame(self, width=350, height=150, pady=50)
        self.lobby_frame.pack()

        # head label
        label = Label(self.lobby_frame, text='Welcome', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=4, sticky=NSEW)
        # game sessions
        self.sessionlist = Listbox(self.lobby_frame, height=10)
        self.sessionlist.grid(row=1, column=0, columnspan=4, sticky=NSEW)
        # JOIN button
        self.join_button = Button(self.lobby_frame, text='Join', command=self.join)
        self.join_button.grid(row=2, column=0, sticky=NSEW)
        # CREATE button
        self.create_button = Button(self.lobby_frame, text='Create new', command=self.create)
        self.create_button.grid(row=2, column=1, sticky=NSEW)
        # REFRESH button
        self.refresh_butoon = Button(self.lobby_frame, text='Refresh', command=self.prepare)
        self.refresh_butoon.grid(row=2, column=2, sticky=NSEW)
        # quit button
        self.quit_button = Button(self.lobby_frame, text='Quit', command=self.quit_client)
        self.quit_button.grid(row=2, column=3, sticky=NSEW)
        logging.debug('Loading *Lobby* Page success!')

    def prepare(self):
        # clear room info
        self.sessionlist.delete(0, END)
        # get room info
        rsp = self.controller.user.call(REQ_getRoom, '')
        if rsp == MSG_SEP:
            data = 'No game session yet'
            self.sessionlist.insert(END, data)
            return
        else:
            rooms = rsp.split(MSG_SEP)
            rooms = rooms[:-1]  # del last empty str
            for room in rooms:
                roominfo = room.split(DTA_SEP)
                data = roominfo[0] + '   limit: ' + roominfo[1] + '/' + roominfo[2]
                self.sessionlist.insert(END, data)
        return

    def join(self):
        # join game session
        # get selection
        id = [self.sessionlist.get(idx) for idx in self.sessionlist.curselection()]
        id = id[0]  # get first element in list
        id = id[0]  # get first character in element
        # send request
        req = id + MSG_SEP + self.controller.user.name
        rsp = self.controller.user.call(REQ_JOIN, req)
        if rsp == RSP_OK:
            logging.debug('[*] Game ID is: %s' % id)
            self.controller.user.gameid = int(id)
            # prepare sudoku
            frame = self.controller.frames['Gamesession']
            frame.prepare()
            # turn page
            self.controller.show_frame("Gamesession")
        else:
            tkMessageBox.showwarning('Error occurred', 'This room is already full!')
        return

    def create(self):
        # create new game session
        self.controller.show_frame("Newroom")
        return

    def quit_client(self):
        # quit at server side
        req = '0' + MSG_SEP + self.controller.user.name
        rsp = self.controller.user.call(REQ_QUIT, req)
        # close connection
        self.controller.user.connection.close()
        self.quit()
        return


# **NEWROOM**---------------------------------------------------------------------------------------
class Newroom(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'newroom' Frame
        self.newroom_frame = Frame(self, width=350, height=150, pady=50)
        self.newroom_frame.pack()
        # variables
        DIFFICULTY = ['easy', 'medium', 'hard']
        self.diffi_var = StringVar()

        # head label
        label = Label(self.newroom_frame, text='Create your Sudoku', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        # difficulty
        self.diffi_label = Label(self.newroom_frame, text='Select Difficulty:')
        self.diffi_label.grid(row=1, column=0, sticky=NSEW)
        self.diffi_menu = OptionMenu(self.newroom_frame, self.diffi_var, *DIFFICULTY)
        self.diffi_menu.grid(row=1, column=1, sticky=NSEW)

        # limitation
        self.limit_label = Label(self.newroom_frame, text='Player Limitation:')
        self.limit_label.grid(row=2, column=0, sticky=NSEW)
        self.limit_entry = Entry(self.newroom_frame)
        self.limit_entry.grid(row=2, column=1, sticky=NSEW)

        # button
        self.submit_button = Button(self.newroom_frame, text='Submit', command=self.create)
        self.submit_button.grid(row=3, column=0, sticky=NSEW)
        self.back_button = Button(self.newroom_frame, text='Back', command=self.back)
        self.back_button.grid(row=3, column=1, sticky=NSEW)

    def create(self):
        # create game session
        # get difficulty & limitation number
        diffi = self.diffi_var.get()
        limit = self.limit_entry.get()
        try:
            int(limit)
        except ValueError as e:
            tkMessageBox.showwarning('Error occurred', 'Please input integer number!')
            self.limit_entry.delete(0, END)
            return
        logging.debug('[*] Sudoku mode: %s' % diffi)
        logging.debug('[*] Game limitation: %s' % limit)
        # send req
        req = diffi + MSG_SEP + limit + MSG_SEP + self.controller.user.name
        rsp = self.controller.user.call(REQ_CREATE, req)
        # set game id
        self.controller.user.gameid = int(rsp)
        logging.debug('[*] Game ID is: %s' % rsp)
        # prepare sudoku
        frame = self.controller.frames['Gamesession']
        frame.prepare()
        # turn page
        self.controller.show_frame("Gamesession")
        return

    def back(self):
        # back to lobby
        self.limit_entry.delete(0, END)
        self.controller.show_frame("Lobby")
        return


# **Gamesession**---------------------------------------------------------------------------------------
class Gamesession(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'Gamesession' Frame
        self.game_header_frame = Frame(self, width=350, height=100)
        self.game_content_frame = Frame(self, width=350, height=300)
        self.game_footer_frame = Frame(self, width=100, height=50, padx=100)

        self.game_header_frame.grid(row=0, column=0, sticky=NSEW)
        self.game_content_frame.grid(row=1, column=0, sticky=NSEW)
        self.game_footer_frame.grid(row=2, column=0, sticky=NSEW)
        self.game_header_frame.grid_propagate(0)
        self.game_content_frame.grid_propagate(0)
        self.game_footer_frame.grid_propagate(0)

        """Variables"""
        self.welcome = StringVar()
        self.welcome.set('Waiting opponents...')

        """header frame"""
        # Slogan welcome
        label = Label(self.game_header_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=16, sticky=NSEW, padx=(75, 75))

        """footer frame"""
        # submit
        self.submit_button = Button(self.game_footer_frame, text='Submit', command=self.submit_move, width=6)
        self.submit_button.grid(row=0, column=0, sticky=NSEW)
        self.submit_button.configure(state='disabled')  # waiting for game start
        # quit
        self.exit_button = Button(self.game_footer_frame, text='Quit', command=self.quit_game, width=6)
        self.exit_button.grid(row=0, column=1, sticky=NSEW)
        # notifications
        pass

        """content frame"""
        # sudoku setup
        self.puzzle = []
        self.entries = {}
        self.puzzle_labels = []

        logging.debug('Loading *GameSession* Page success!')

    def prepare(self):
        # prepare sudoku & ui
        return

    def update_user(self):
        return

    def update_sudoku(self):
        # clear ui
        pass
        # send req
        pass
        # update ui
        count = 0
        for i in range(9):
            for j in range(9):
                if self.puzzle[count] == '_':
                    insert_entry = Entry(self.game_content_frame, width=3)
                    insert_entry.grid(row=i, column=j, sticky=NSEW)
                    self.entries[insert_entry] = count
                else:
                    insert_label = Label(self.game_content_frame, text=self.puzzle[count])
                    insert_label.grid(row=i, column=j, sticky=NSEW)
                    self.puzzle_labels.append(insert_label)
                count += 1
        return

    def submit_move(self):
        return

    def quit_game(self):
        return


"""---------------------------------------------------------------------------------------------------------------------
                                            MAIN
---------------------------------------------------------------------------------------------------------------------"""
if __name__ == '__main__':
    app = Client()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logging.warn('User terminated client!')
