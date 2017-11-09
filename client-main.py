"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                                          Sudoku Game Client

                     Team member: Andro Lominadze, Kadir Aktas, Xatia Kilanava, Shan Wu

                     cites: (finish later)


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
"""------------------------------------------------------------------------------------------------------------
                                          Question & Changes
                                          
Q: How to avoid duplicated names?                                          
A: Every game login first, then create name. That may cause the same name in the same game. So in this game, 
   we enter server info FIRST to ensure no duplicated names.
   
For next meetup:
Q: fetch sudoku just list or string, notification sudoku, function reuse..

------------------------------------------------------------------------------------------------------------"""

"""------------------------------------------------------------------------------------------------------------
                                        Personal note(delete later)
                                        
change data type of sudoku, userinfos -> need to change in UI function
self.users = 'user1/0:user2/5:user3/10'
line 514: example game data
line 630: example user data
line 653: example sudoku data
------------------------------------------------------------------------------------------------------------"""
from Tkinter import *
import tkMessageBox
import tkFont as tkfont
import ttk
import re
import logging
import threading
import client_protocol
from socket import AF_INET, SOCK_STREAM, socket, timeout
import sudoku_generator  # for test

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(threadName)-2s) %(message)s', )

"""------------------------------------------------------------------------------------------------------------
                                            User info class

           store local game data: current name, previous name, self score, game id, client socket.
------------------------------------------------------------------------------------------------------------"""


class Userinfo():
    def __init__(self):
        self.currentname = ''
        self.names = ['Or select your previous names', ]
        self.score = 0
        self.gameid = 0
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.notifi_thread = []
        self.game_frame = []

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


"""------------------------------------------------------------------------------------------------------------
                                        The end of User info class
------------------------------------------------------------------------------------------------------------"""

"""------------------------------------------------------------------------------------------------------------
                                    communicate with server Kadir's work

Funtions: makeconnection, checkname, fetch_sudoku*, fetch_user*, joingame, create_game, attempt, quit_game
Other func: cut_down

* -> not complete
------------------------------------------------------------------------------------------------------------"""


def checkname(usr, n):
    rsp_hdr = ''
    check = True
    msg = client_protocol.__REQ_REG + client_protocol.MSG_SEP + n
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, msg)

    if rsp_hdr == client_protocol.__RSP_OK:
        # already set current name in UI..
        check = True
        if n not in usr.names:
            usr.names.append(n)
    else:
        check = False
    return check


def makeconnection(usr, addr, port):
    # print addr, int(port)
    check = True
    server_address = (addr, int(port))  # not sure  -R: you are right:)
    usr.socket.settimeout(10)
    try:
        logging.debug('Trying to connect server!')
        usr.socket.connect(server_address)
        usr.socket.settimeout(None)
        check = True
    except timeout:
        logging.debug('Connection time out!')
        check = False  # set back to False after test

    return check


def joingame(usr, gid):
    check = True

    message = client_protocol.__REQ_JOIN + client_protocol.MSG_SEP + str(gid) + usr.currentname
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        check = True
        usr.gameid = gid
    else:
        check = False

    return check


def create_game(usr, diffi, limit):
    check = True

    message = client_protocol.__REQ_JOIN + client_protocol.MSG_SEP + usr.currentname + client_protocol.DATA_SEP + limit + client_protocol.DATA_SEP + diffi
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        gid = int(rsp_msg)
        usr.gameid = gid
    else:
        gid = -1

    return gid


def attempt(usr, gid, place, number):
    check = True

    message = client_protocol.__REQ_MOVE + client_protocol.MSG_SEP + str(
        gid) + client_protocol.DATA_SEP + usr.currentname + client_protocol.DATA_SEP + str(
        place) + client_protocol.DATA_SEP + str(number)
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        check = True
    else:
        check = False

    return check


def quit_game(usr):
    check = True

    message = client_protocol.__REQ_QUIT + client_protocol.MSG_SEP + str(
        usr.gameid) + client_protocol.DATA_SEP + usr.currentname
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        check = True
    else:
        check = False

    return check


def fetch_sudoku(usr):
    message = client_protocol.__REQ_SUDOKU + client_protocol.MSG_SEP
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        check = True
    else:
        check = False

    return check, rsp_msg


def fetch_user(usr):
    message = client_protocol.__REQ_USER + client_protocol.MSG_SEP + usr.gameid
    rsp_hdr, rsp_msg = client_protocol.publish(usr.socket, message)

    if rsp_hdr == client_protocol.__RSP_OK:
        check = True
        user = rsp_msg[0]
        scores = rsp_msg[2:]
    else:
        check = False
        user = ""
        scores = ""

    return check, user, scores


def cut_down(usr, user):  # finish later (close connection)
    return True


"""------------------------------------------------------------------------------------------------------------
                                    The end of communication functions
------------------------------------------------------------------------------------------------------------"""

"""------------------------------------------------------------------------------------------------------------
                                      Notification Thread function
------------------------------------------------------------------------------------------------------------"""


def notification_thread(usr, Frame):
    pass


"""------------------------------------------------------------------------------------------------------------
                                     The end of Notification Thread
------------------------------------------------------------------------------------------------------------"""

"""------------------------------------------------------------------------------------------------------------
                                    Client UI & operating functions
                                    
        Main classes: Client(base, parent), ConnectServer, Login, Joining, NewSession, GameSession
        
------------------------------------------------------------------------------------------------------------"""


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
            frame = F(master=container, controller=self)
            self.frames[page_name] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConnectServer")
        self.user.game_frame.append(self.frames[GameSession.__name__])

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


# **ConnectServer**---------------------------------------------------------------------------------------
class ConnectServer(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'ConnectServer' Frame
        self.consrv_frame = Frame(self, width=500, height=150, pady=50)
        self.consrv_frame.pack()
        # variables
        self.IP_entry_var = StringVar()
        self.port_entry_var = StringVar()

        # head label
        label = Label(self.consrv_frame, text='Connect to the server first:)', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # server IP label&entry
        IP_label = Label(self.consrv_frame, text='Server IP address:')
        self.IP_entry = Entry(self.consrv_frame, textvariable=self.IP_entry_var)
        IP_label.grid(row=2, column=0, sticky=W)
        self.IP_entry.grid(row=2, column=1, sticky=W)
        self.IP_entry.focus()
        self.IP_entry.bind('<Return>', self.enterbtn)
        # server port label&entry
        port_label = Label(self.consrv_frame, text='Server port:')
        self.port_entry = Entry(self.consrv_frame, textvariable=self.port_entry_var)
        port_label.grid(row=4, column=0, sticky=W)
        self.port_entry.grid(row=4, column=1, sticky=W)
        self.port_entry.bind('<Return>', self.enterbtn)
        # submit button
        self.submit_button = Button(self.consrv_frame, text='Connnect', command=self.connect)
        self.submit_button.grid(row=5, column=0, columnspan=2, sticky=NSEW)
        self.quit_button = Button(self.consrv_frame, text='Quit', command=self.quit)
        self.quit_button.grid(row=6, column=0, columnspan=2, sticky=NSEW)
        logging.debug('Loading *Connectserver* Page success!')

    def connect(self):
        serveraddr = ''
        serverport = 0
        try:
            serveraddr = self.IP_entry.get()
            serverport = int(self.port_entry.get())
            # use re match
            serveraddr_match = re.search(
                '((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))',
                serveraddr)
            if not serveraddr_match:
                logging.debug('Address value error!')
                tkMessageBox.showwarning('Input Error', 'Server address error!')
                self.IP_entry_var.set('')
                self.port_entry_var.set('')
                self.IP_entry.focus()
                return 0
        except ValueError:
            logging.debug('Port value error!')
            tkMessageBox.showwarning('Input Error', 'Port number error!')
            self.IP_entry_var.set('')
            self.port_entry_var.set('')
            self.IP_entry.focus()
            return 0

        # connect to server
        if makeconnection(self.controller.user, serveraddr_match.group(), serverport):
            logging.debug('Connected to server!')
            self.controller.show_frame("Login")
        else:
            logging.debug('Connecting timeout! Please check your input!')
            tkMessageBox.showwarning('Connection Error', 'Connecting failed! Please check your input!')
            self.IP_entry_var.set('')
            self.port_entry_var.set('')
            self.IP_entry.focus()

    def enterbtn(self, e):
        self.connect()


# **Login**-------------------------------------------------------------------------------------------------------------
class Login(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller

        # User profile
        self.name = StringVar()
        self.name_entry = StringVar()
        self.old_names_var = StringVar()
        self.old_names_var.set('Or select your previous names')
        """login page"""
        # login frameg
        self.login_frame = Frame(self, width=500, height=150, pady=50)
        self.login_frame.pack()
        # input label
        self.login_name_label = Label(self.login_frame, text='Please input your user name:', font=controller.title_font)
        self.login_name_label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # username entry
        self.login_name_entry = Entry(self.login_frame, textvariable=self.name_entry)
        self.login_name_entry.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        # older names
        OLD_NAMES = self.controller.user.getoldnames()
        self.option_menu = OptionMenu(self.login_frame, self.old_names_var, *OLD_NAMES)
        self.option_menu.grid(row=2, column=0, columnspan=2, sticky=NSEW)
        self.refresh_oldname()
        # self.login_name_entry.focus()
        self.login_name_entry.bind('<Return>', self.enterbtn)
        # submit button
        self.login_submit_button = Button(self.login_frame, text='Submit', command=self.check_username)
        self.login_submit_button.grid(row=3, column=0)
        self.login_quit_button = Button(self.login_frame, text='Quit', command=self.quit_conection)
        self.login_quit_button.grid(row=3, column=1)
        # foot label
        self.login_foot_label = Label(self.login_frame, text='No more than 8 characters. No special symbols.')
        self.login_foot_label.grid(row=4, column=0, columnspan=2, sticky=NSEW)

        logging.debug('Loading *Login* Page success!')

    def check_username(self):
        # whether use previous name?
        if self.old_names_var.get() != 'Or select your previous names':
            self.name = self.old_names_var.get()
            self.old_names_var.set('')
        else:
            # get input name
            self.name = self.login_name_entry.get()
        try:
            check = re.search('\w+', self.name, flags=0).group()
            if check == str(self.name):
                logging.debug('Player name set to %s!. Checking on server' % self.name)
                # check name on server..
                if checkname(self.controller.user, check):
                    logging.debug('Name ok!')
                    tkMessageBox.showinfo('Welcome', 'Welcome to Sudoku game! %s' % self.name)
                    self.controller.user.setname(self.name)  # store user info
                    self.controller.show_frame("Joining")
                else:
                    logging.debug('Name Error: Duplicated username on server!')
                    tkMessageBox.showwarning('Name Error', 'Duplicated username on server!')
                    self.name_entry.set('')
                    self.login_name_entry.focus()
            else:
                logging.debug('Name Error: Illegal username!')
                tkMessageBox.showwarning('Name Error', 'Illegal username!')
                self.name_entry.set('')
                self.login_name_entry.focus()
        except AttributeError as e:
            logging.debug('Name Error: No character input!')
            tkMessageBox.showwarning('Name Error', 'No character input!')
            self.name_entry.set('')
            self.login_name_entry.focus()

    def enterbtn(self, e):
        self.check_username()

    def refresh_oldname(self):
        logging.debug('refreshing old names')
        self.option_menu.destroy()
        OLD_NAMES = self.controller.user.getoldnames()
        self.option_menu = OptionMenu(self.login_frame, self.old_names_var, *OLD_NAMES)
        self.option_menu.grid(row=2, column=0, columnspan=2, sticky=NSEW)
        self.option_menu.after(60000, self.refresh_oldname)

    def quit_conection(self):
        if tkMessageBox.askyesno('Quit?', 'Are you sure to quit?'):
            name = self.controller.user.getname()
            if name == '':
                logging.debug('Bye:)')
                self.quit()
            else:
                if cut_down(self.controller.user, name):
                    logging.debug('Bye:)')
                    self.quit()


# **Joining**----------------------------------------------------------------------------------------------------------
# after get gid, fetch game first, render game, then jump page
class Joining(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('Please select your game session!')
        """Joining page"""
        # Joing frame
        self.join_frame = Frame(self, width=500, height=150, pady=50)
        self.join_frame.pack()
        # Slogan welcome
        label = Label(self.join_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=3, sticky=NSEW)
        # session table tree
        self.tree = ttk.Treeview(self.join_frame, selectmode='browse', show='headings', height=10, columns=('a', 'b'))
        self.tree.column('a', width=50, anchor='center')
        self.tree.column('b', width=50, anchor='center')
        self.tree.heading('a', text='Game ID')
        self.tree.heading('b', text='Players')
        self.loadgames()
        self.tree.grid(row=1, column=0, columnspan=3, sticky=NSEW)
        self.tree.bind('<Return>', self.select)
        logging.debug('Loading *Joining* Page success!')
        # button
        self.select_button = Button(self.join_frame, text='Select', command=self.select)
        self.select_button.grid(row=2, column=0)
        self.create_button = Button(self.join_frame, text='Create new', command=self.create)
        self.create_button.grid(row=2, column=1)
        self.fetch_button = Button(self.join_frame, text='Fetch sessions', command=self.loadgames)
        self.fetch_button.grid(row=2, column=2)

    def select(self, e=None):
        try:
            item = self.tree.selection()[0]
            itemtup = self.tree.item(item, 'values')
            gameid = int(itemtup[0])
            if joingame(self.controller.user, gameid):
                logging.debug('User selected game ID: %d.' % gameid)

                """Start notification thread"""
                game_frame = self.controller.user.game_frame[0]
                start_notification = threading.Thread(target=notification_thread,
                                                      args=(self.controller.user, game_frame))
                self.controller.user.notifi_thread.append(start_notification)

                """fetch sudoku game session, user_data, rendering"""

                self.controller.show_frame("GameSession")
            else:
                logging.debug('Game session is full!')
                tkMessageBox.showwarning('Can not join game',
                                         'The game session you selected is full! Please choose another one.')
        except IndexError:
            logging.debug('User didn''t select the game session!')
            tkMessageBox.showwarning('Didn''t get game ID', 'Please select at least one game or create new one!')

    def create(self):
        logging.debug('Create new session')
        self.controller.show_frame("NewSession")

    def loadgames(self):
        # delete old items
        for _ in map(self.tree.delete, self.tree.get_children('''''')):
            pass
        # fetch new
        self.games = '1/[0,0,0,0]/3/2:2/[1,0,1,0]/5/1:3/[0,2,2,0]/2/2'  # just example
        # append to tree
        splited_game = self.games.split(client_protocol.MSG_SEP)
        for eachgame in splited_game:
            gameinfo = eachgame.split(client_protocol.DATA_SEP)
            self.tree.insert('', 'end', values=(gameinfo[0], gameinfo[3] + '/' + gameinfo[2]))
        self.tree.after(30000, self.loadgames)  # refresh every 30s
        logging.debug('Refreshing game sessions every 30s.')


# **NewSession**-----------------------------------------------------------------------------------------------------
# fetch game first, then jump
class NewSession(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('Create your sudoku!')
        # Joing frame
        self.new_frame = Frame(self, width=500, height=150, pady=50)
        self.new_frame.pack()
        # Slogan welcome
        label = Label(self.new_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)

        """select difficulty mode(label, optionmenu, button) & limit num"""
        # label
        self.diffi_label = Label(self.new_frame, text='Select Difficulty:')
        self.diffi_label.grid(row=1, column=0)
        self.limit_label = Label(self.new_frame, text='Player limitation:')
        self.limit_label.grid(row=2, column=0)
        # optionmenu
        DIFFICULTY = ['easy', 'medium', 'hard']
        self.diffi_var = StringVar()
        self.option_menu = OptionMenu(self.new_frame, self.diffi_var, *DIFFICULTY)
        self.option_menu.grid(row=1, column=1, sticky=NSEW)
        # limit entry
        self.limit_entry_var = StringVar()
        self.limit_entry = Entry(self.new_frame, textvariable=self.limit_entry_var)
        self.limit_entry.grid(row=2, column=1)
        # button
        self.submit_button = Button(self.new_frame, text='Submit', command=self.create_game)
        self.submit_button.grid(row=3, column=1, sticky=NSEW)
        self.back_button = Button(self.new_frame, text='Back', command=self.go_back)
        self.back_button.grid(row=3, column=0, sticky=NSEW)

        # bind enter key
        self.limit_entry.bind('<Return>', self.PressReturn)
        logging.debug('Loading *NewSession* Page success!')

    def create_game(self):
        try:
            diffi = self.diffi_var.get()
            limit = self.limit_entry_var.get()
            logging.debug('User selected the mode: %s' % diffi)
            logging.debug('Player limitation is: %d' % limit)
            gid = create_game(self.controller.user, diffi, limit)
            if gid == -1:
                logging.debug('An error occured when creating game!')
                tkMessageBox.showwarning('GID Value Error', 'Please create game later!')
            else:
                logging.debug('Game session created! Game id is %d.' % gid)

                """fetch sudoku game, user_data, rendering"""


                """Start notification thread"""
                game_frame =  self.controller.user.game_frame[0]
                start_notification = threading.Thread(target=notification_thread,
                args=(self.controller.user, game_frame))
                self.controller.user.notifi_thread.append(start_notification)

                self.controller.show_frame("GameSession")
        except ValueError:
            logging.debug('User didn''t input right limit number!')
            tkMessageBox.showwarning('Value Error', 'Please input right limit number!')
            self.limit_entry_var.set('')
            self.limit_entry.focus()

    def go_back(self):
        logging.debug('Go back to Game selection!')
        self.controller.show_frame("Joining")

    def PressReturn(self, e):
        self.create_game()


# **GameSession**---------------------------------------------------------------------------------------------------
# update_score update_sudoku -> user, puzzle data type
class GameSession(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # get user info
        self.user = self.controller.user
        self.answer = []
        self.puzzle = []
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('Waiting other players!')

        """Joing frame, header, content, footer frames"""
        self.game_frame = Frame(self)
        self.game_header_frame = Frame(self.game_frame, width=500, height=100)
        self.game_content_frame = Frame(self.game_frame, width=500, height=300)
        self.game_footer_frame = Frame(self.game_frame, width=500, height=50)

        self.game_frame.pack()
        self.game_header_frame.grid(row=0, column=0, sticky=NSEW, padx=50)
        self.game_content_frame.grid(row=1, column=0, sticky=NSEW, padx=50)
        self.game_footer_frame.grid(row=2, column=0, sticky=NSEW, padx=50)
        self.game_header_frame.grid_propagate(0)
        self.game_content_frame.grid_propagate(0)
        self.game_footer_frame.grid_propagate(0)

        """header frame"""
        # Slogan welcome
        label = Label(self.game_header_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # fetch & display users
        self.user_data = 'user1/0:user2/5:user3/10'  # example user data
        self.score_labels = []
        score_board = self.user_data.split(client_protocol.MSG_SEP)
        row, column = 1, 0
        for each_user in score_board:
            name, score = each_user.split(client_protocol.DATA_SEP)
            name_label = Label(self.game_header_frame, text=name + ':')
            score_label = Label(self.game_header_frame, text=score)
            name_label.grid(row=row, column=column % 2, sticky=E)
            column += 1
            score_label.grid(row=row, column=column % 2, sticky=W)
            row += 1
            column += 1
            self.score_labels.append(name_label)
            self.score_labels.append(score_label)

        """footer frame"""
        # submit
        self.submit_button = Button(self.game_footer_frame, text='Submit', command=self.submit_move)
        self.submit_button.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # quit
        self.exit_button = Button(self.game_footer_frame, text='Quit', command=self.quit)
        self.exit_button.grid(row=0, column=1, columnspan=2, sticky=NSEW)

        """content frame"""
        # sudoku (label & entry)
        self.generate_example()
        count = 0
        self.entries = {}
        self.puzzle_labels = []
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

        logging.debug('Loading *GameSession* Page success!')

    def update_scores(self, users):  # user string (or list)
        # delete old widgets
        for eachlabel in self.score_labels:
            eachlabel.destory()
        # update new widgets
        self.user_data = users
        self.score_labels = []
        score_board = self.user_data.split(client_protocol.MSG_SEP)
        row, column = 1, 0
        for each_user in score_board:
            name, score = each_user.split(client_protocol.DATA_SEP)
            name_label = Label(self.game_header_frame, text=name + ':')
            score_label = Label(self.game_header_frame, text=score)
            name_label.grid(row=row, column=column % 2, sticky=E)
            column += 1
            score_label.grid(row=row, column=column % 2, sticky=W)
            row += 1
            column += 1
            self.score_labels.append(name_label)
            self.score_labels.append(score_label)
        pass

    def update_sudoku(self, puzzle):  # puzzle list
        # delete old widgets
        for eachlabel in self.puzzle_labels:
            eachlabel.destory()
        entry_widgets = self.entries.keys()
        for eachentry in entry_widgets:
            eachentry.destory()
        # update new widgets
        self.puzzle = []
        self.entries = {}
        self.puzzle_labels = []
        for n in puzzle:
            self.puzzle.append(n)
        count = 0
        for i in range(9):
            for j in range(9):
                if self.puzzle[count] == '_':
                    insert_entry = Entry(self.game_content_frame, width=3, textvariable=self.entry_var)
                    insert_entry.grid(row=i, column=j, sticky=NSEW)
                    self.entries[insert_entry] = count
                else:
                    insert_label = Label(self.game_content_frame, text=self.puzzle[count])
                    insert_label.grid(row=i, column=j, sticky=NSEW)
                    self.puzzle_labels.append(insert_label)
                count += 1

    def submit_move(self):  # entries={entry:pos, } modified_entry={entry:value}
        self.modified_entries = {}
        entries = self.entries.keys()
        for eachentry in entries:
            value = eachentry.get()
            if value != '':
                self.modified_entries[eachentry] = value

        if len(self.modified_entries) > 1:
            tkMessageBox.showwarning('Too many entries', 'Please make exactly one entry!')
            self.entry_var.set('')
            return 0

        entries = self.modified_entries.keys()
        position = self.entries[entries[0]]
        inputvalue = self.modified_entries[entries[0]]
        print 'you inputed %s, postion: %d' % (inputvalue, position)
        return 1


    def quit(self):
        if tkMessageBox.askyesno('Are you sure to quit?', 'If you quit the game, you will lose all the points!'):
            logging.debug('Player has quit the game session!')
            if quit_game(self.controller.user):
                self.controller.show_frame("Login")

    def generate_example(self):
        # example sudoku
        answer, puzzle = sudoku_generator.setup_sudoku('easy')
        for n in answer:
            self.answer.append(n)
        for n in puzzle:
            self.puzzle.append(n)


"""-----------------------------------------------------------------------------------------------------------------
                                        Client Main Function
                                        
                                create client instance, run UI in loop
-----------------------------------------------------------------------------------------------------------------"""
if __name__ == '__main__':
    app = Client()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logging.debug('User terminated client!')
