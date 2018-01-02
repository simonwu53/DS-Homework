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
                                          User info
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
        number = int(id[11])
        limit = int(id[13])
        id = id[0]  # get first character in element
        # send request
        req = id + MSG_SEP + self.controller.user.name
        rsp = self.controller.user.call(REQ_JOIN, req)
        if rsp == RSP_OK:
            logging.debug('[*] Game ID is: %s' % id)
            self.controller.user.gameid = int(id)
            # set limit
            self.controller.user.limit = limit
            self.controller.user.number = number + 1
            # prepare sudoku
            frame = self.controller.frames['Gamesession']
            frame.prepare()
            if self.controller.user.limit == self.controller.user.number:
                frame.start_game()
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
        # set limitation
        self.controller.user.limit = int(limit)
        self.controller.user.number = 1
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
        self.user_labels = []
        self.score = StringVar()
        self.name = StringVar()
        self.score.set(str(self.controller.user.score))
        self.name.set('')
        self.name_label = Label(self.game_header_frame, textvariable=self.name)
        self.score_label = Label(self.game_header_frame, textvariable=self.score)
        self.name_label.grid(row=1, column=0, sticky=NSEW)
        self.score_label.grid(row=1, column=1, sticky=W)

        """footer frame"""
        # submit
        self.submit_button = Button(self.game_footer_frame, text='Submit', command=self.submit_move, width=6)
        self.submit_button.grid(row=0, column=0, sticky=NSEW)
        self.submit_button.configure(state='disabled')  # waiting for game start
        # quit
        self.exit_button = Button(self.game_footer_frame, text='Quit', command=self.quit_game, width=6)
        self.exit_button.grid(row=0, column=1, sticky=NSEW)
        # notifications
        self.notify_var = StringVar()
        self.notify_var.set('')
        self.noti_label = Label(self.game_footer_frame, textvariable=self.notify_var)
        self.noti_label.grid(row=1, column=0, columnspan=2, sticky=NSEW)

        """content frame"""
        # sudoku setup
        self.puzzle = []
        self.entries = {}
        self.puzzle_labels = []

        logging.debug('Loading *GameSession* Page success!')

    def prepare(self):
        # prepare sudoku & ui
        self.update_user()
        self.update_sudoku()
        return

    def update_user(self):
        # clear ui
        for eachlabel in self.user_labels:
            eachlabel.destroy()
        # send req
        userdata = self.controller.user.call(REQ_getUser, self.controller.user.gameid)
        userdata = userdata.split(MSG_SEP)
        userdata = userdata[:-1]
        # update ui
        row, column = 1, 2
        for eachuser in userdata:
            name, score = eachuser.split(DTA_SEP)
            if name == self.controller.user.name:
                self.name.set(name + ':')
            else:
                name_label = Label(self.game_header_frame, text=name + ':')
                score_label = Label(self.game_header_frame, text=score)
                name_label.grid(row=row, column=column, sticky=NSEW)
                score_label.grid(row=row, column=column + 1, sticky=W)
                column += 2
                self.user_labels.append(name_label)
                self.user_labels.append(score_label)
        return

    def update_sudoku(self):
        # clear ui
        for eachlabel in self.puzzle_labels:
            eachlabel.destroy()
        for eachentry in self.entries.keys():
            eachentry.destroy()
        # send req
        sudoku = self.controller.user.call(REQ_getSudoku, self.controller.user.gameid)
        self.puzzle = list(sudoku)
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
        modified_entries = {}
        entries = self.entries.keys()
        for eachentry in entries:
            value = eachentry.get()
            if value != '':
                if not value.isdigit():
                    tkMessageBox.showwarning('Not a digit?', 'Please input a number!')
                    return
                else:
                    modified_entries[eachentry] = value

        if len(modified_entries) > 1:
            tkMessageBox.showwarning('Too many entries', 'Please make exactly one entry!')
            return
        elif len(modified_entries) == 0:
            tkMessageBox.showwarning('No entry', 'Please fill one entry first!')
            return

        entries = modified_entries.keys()
        position = self.entries[entries[0]]
        inputvalue = modified_entries[entries[0]]
        msg = str(self.controller.user.gameid) + MSG_SEP + str(
            position) + MSG_SEP + inputvalue + MSG_SEP + self.controller.user.name
        # send req
        rsp = self.controller.user.call(REQ_MOVE, msg)
        # change score
        if rsp == RSP_OK:  # correct
            self.controller.user.score += 1
        elif rsp == RSP_ERR:
            self.controller.user.score -= 1
        elif rsp == RSP_LATE:
            tkMessageBox.showwarning('Late', 'You are late!')
        self.score.set(str(self.controller.user.score))
        return

    def quit_game(self):
        # send req
        msg = str(self.controller.user.gameid) + MSG_SEP + self.controller.user.name
        rsp = self.controller.user.call(REQ_QUIT, msg)
        if rsp == RSP_OK:
            frame = self.controller.frames['Lobby']
            frame.prepare()
            self.controller.show_frame("Lobby")
        else:
            tkMessageBox.showwarning('Error occurred', 'Please try again!')
        return

    def start_game(self):
        self.welcome.set('Game Started!')
        self.submit_button.configure(state='normal')
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
