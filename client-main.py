"""
MAIN STRUCTURE: GUI -> **Tkinter** contains __ pages -> {Client(base), Login, Joining, Waiting, Playing, Result}
User data stored in class **Userinfo**. And use this class to talk to server. (Tkinter for logic, Userinfo give function)
"""
"""
Every game login first, then create character and name. So in this game, we enter server info FIRST to ensure no 
duplicated names.
"""
from Tkinter import *
import tkMessageBox
import tkFont as tkfont
import ttk
import re
import logging
import client_protocol
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(threadName)-2s) %(message)s',)


class Userinfo():
    def __init__(self):
        self.currentname = ''
        self.names = ['Peter', 'James', 'Curry']   # example
        self.score = 0
        self.gameid = 0
        #self.socket =
        # create socket

    """set methods"""
    def setname(self, n):
        self.currentname = n
        self.names.append(self.currentname)

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

    """communicate with server Kadir's work"""
    def checkname(self, n):  # finish later
        examplecheck = True
        return examplecheck

    def fetchgames(self):  # finish later (deal problem before connect to server)
        examplegames = {1:[[0,0,0,0],3],
                        2:[[1,0,1,0],5],
                        3:[[0,2,2,0],2]}
        exampleusers = {1: {'Jerry': 5, 'Tom': 0},
                        2: {'Simon': 0},
                        3: {'Kitty': 10, 'Michael': 12}}
        return examplegames, exampleusers

    def makeconnection(self, addr, port):
        print addr, int(port)  # finish later
        return True

    def joingame(self, gid):  # finish later
        self.gameid = gid  # only when join succussfully/ create game
        return True

    def create_game(self, diffi, limit): # finish later
        return 2

    def quit_game(self, user, gid): # finish later (delete username on server)
        return True

    def cut_down(self, user): #finish later (close connection)
        return True


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

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


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
        self.login_frame = Frame(self, width=300, height=150)
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
        #self.login_name_entry.focus()
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
        else:
            # get input name
            self.name = self.login_name_entry.get()
        try:
            check = re.search('\w+', self.name, flags=0).group()
            if check == str(self.name):
                logging.debug('Player name set to %s!. Checking on server' % self.name)
                # check name on server..
                if self.controller.user.checkname(check):
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
        except AttributeError:
            logging.debug('Name Error: No character input!')
            tkMessageBox.showwarning('Name Error', 'No character input!')
            self.name_entry.set('')
            self.login_name_entry.focus()

    def enterbtn(self, e):
        self.check_username()

    def quit_conection(self):
        if tkMessageBox.askyesno('Quit?', 'Are you sure to quit?'):
            name = self.controller.user.getname()
            if name == '':
                logging.debug('Bye:)')
                self.quit()
            else:
                if self.controller.user.cut_down(name):
                    logging.debug('Bye:)')
                    self.quit()


class ConnectServer(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'ConnectServer' Frame
        self.consrv_frame = Frame(self, width=300, height=150)
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
            serveraddr_match = re.search('((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d))))', serveraddr)
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
        if self.controller.user.makeconnection(serveraddr_match.group(), serverport):
            logging.debug('Connected to server!')
            self.controller.show_frame("Login")
        else:
            logging.debug('Connecting failed! Please check your input!')
            tkMessageBox.showwarning('Connection Error', 'Connecting failed! Please check your input!')
            self.IP_entry_var.set('')
            self.port_entry_var.set('')
            self.IP_entry.focus()

    def enterbtn(self, e):
        self.connect()


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
        self.join_frame = Frame(self, width=300, height=150)
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
        self.tree.bind('<Double-1>', self.OnDoubleClick)
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
            if self.controller.user.joingame(gameid):
                logging.debug('User selected game ID: %d.' % gameid)
                self.controller.show_frame("GameSession")
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
        self.games, self.users = self.controller.user.fetchgames()  # fetch game sessions
        for gameid, gamelist in self.games.iteritems():
            player_limit = gamelist[1]
            namelist = self.users[gameid]
            self.tree.insert('', 'end', values=(gameid, str(len(namelist))+'/'+str(player_limit)))
        self.tree.after(15000, self.loadgames)  # refresh every 15s
        logging.debug('Refreshing game sessions every 15s.')

    """test part"""

    def OnDoubleClick(self, e):
        # First check if a blank space was selected
        entryIndex = self.tree.focus()
        if '' == entryIndex: return

        # Set up window
        win = Toplevel()
        win.title("Edit Entry")
        #win.attributes("-toolwindow", True)

        ####
        # Set up the window's other attributes and geometry
        ####

        # Grab the entry's values
        real_coords = (self.tree.winfo_pointerx() - self.tree.winfo_rootx(),
                       self.tree.winfo_pointery() - self.tree.winfo_rooty())
        item = self.tree.identify('item', *real_coords)
        values = self.tree.item(item, 'values')

        col1Lbl = Label(win, text="Value 1: ")
        col1Ent = Entry(win)
        col1Ent.insert(0, values[0])  # Default is column 1's current value
        col1Lbl.grid(row=0, column=0)
        col1Ent.grid(row=0, column=1)

        col2Lbl = Label(win, text="Value 2: ")
        col2Ent = Entry(win)
        col2Ent.insert(0, values[1])  # Default is column 2's current value
        col2Lbl.grid(row=0, column=2)
        col2Ent.grid(row=0, column=3)

        col3Lbl = Label(win, text="Value 3: ")
        col3Ent = Entry(win)
        col3Ent.insert(0, values[2])  # Default is column 3's current value
        col3Lbl.grid(row=0, column=4)
        col3Ent.grid(row=0, column=5)

        def UpdateThenDestroy():
            if self.ConfirmEntry(self.tree, col1Ent.get(), col2Ent.get(), col3Ent.get()):
                win.destroy()

        okButt = Button(win, text="Ok")
        okButt.bind("<Button-1>", lambda e: UpdateThenDestroy())
        okButt.grid(row=1, column=4)

        canButt = Button(win, text="Cancel")
        canButt.bind("<Button-1>", lambda c: win.destroy())
        canButt.grid(row=1, column=5)

    def ConfirmEntry(self, treeView, entry1, entry2, entry3):
        ####
        # Whatever validation you need
        ####

        # Grab the current index in the tree
        currInd = treeView.index(treeView.focus())

        # Remove it from the tree
        self.DeleteCurrentEntry(treeView)

        # Put it back in with the upated values
        treeView.insert('', currInd, values=(entry1, entry2, entry3))

        return True

    def DeleteCurrentEntry(self, treeView):
        curr = treeView.focus()

        if '' == curr: return

        treeView.delete(curr)


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
        self.new_frame = Frame(self, width=300, height=150)
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
        DIFFICULTY = ['easy', 'medium', 'hard', 'extreme']
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
            limit = int(self.limit_entry_var.get())
            logging.debug('User selected the mode: %s' % diffi)
            logging.debug('Player limitation is: %d' % limit)
            gid = self.controller.user.create_game(diffi, limit)
            if self.controller.user.joingame(gid):
                logging.debug('Game session created!')
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


class GameSession(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # get user info
        self.user = self.controller.user
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('Waiting other players!')
        # Joing frame & other frames
        self.game_frame = Frame(self)
        self.game_header_frame = Frame(self.game_frame, width=300, height=50)
        self.game_content_frame = Frame(self.game_frame, width=300, height=150)
        self.game_footer_frame = Frame(self.game_frame, width=300, height=50)

        self.game_frame.pack()
        self.game_header_frame.grid(row=0, column=0, sticky=NSEW)
        self.game_content_frame.grid(row=1, column=0, sticky=NSEW)
        self.game_footer_frame.grid(row=2, column=0, sticky=NSEW)
        self.game_header_frame.grid_propagate(0)
        self.game_content_frame.grid_propagate(0)
        self.game_footer_frame.grid_propagate(0)
        # Slogan welcome
        label = Label(self.game_header_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # footer button
        self.exit_button = Button(self.game_footer_frame, text='Quit', command=self.quit)
        self.exit_button.grid(row=0, column=0, sticky=NSEW)
        # for test **add quit button**
        testlabel = Label(self.game_frame)

        logging.debug('Loading *GameSession* Page success!')

    def quit(self):
        if tkMessageBox.askyesno('Are you sure to quit?', 'If you quit the game, you will lose all the points!'):
            logging.debug('Player has quit the game session!')
            name = self.user.getname()
            gid = self.user.getgameid()
            if self.user.quit_game(name, gid):
                self.controller.show_frame("Login")


if __name__ == '__main__':
    app = Client()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logging.debug('User terminated client!')
