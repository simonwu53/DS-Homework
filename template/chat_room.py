# User should only join one chat room at the same time. To send msg in other room, he need check out first, then join
# another room. When user quit client, he will also quit the chat room. When he restart client again, he need to join
# chat room again. Server will not keep user data if client closed.
# just make it simple...
from Tkinter import *
import tkMessageBox
import tkFont as tkfont
import ttk
import logging
import pika
import uuid
import threading
import time

# msg sep
MSG_SEP = ':'
DTA_SEP = '/'
SPE_SEP = '/:/'
# control code
CTR_NOT = '0'
CTR_RSP = '1'
# server response
RSP_ERR = '0'
RSP_OK = '1'
RSP_DUP = '2'
# client code
REQ_NAME = '0'
REQ_FECH = '1'
REQ_QUIT = '2'
REQ_USER = '3'
REQ_CRAT = '4'
REQ_INVT = '5'
REQ_JOIN = '6'
REQ_QROM = '7'
REQ_RUSR = '8'
REQ_MSGS = '9'
REQ_PMSG = '$'
"""---------------------------------------------------------------------------------------------------------------------
                                            LOG info
---------------------------------------------------------------------------------------------------------------------"""
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.WARN, format=FORMAT)
LOG = logging.getLogger()

"""---------------------------------------------------------------------------------------------------------------------
                                            User class
---------------------------------------------------------------------------------------------------------------------"""


class User(object):
    def __init__(self, frames):
        self.name = None
        self.response = None
        self.corr_id = None
        self.privatechat = None
        self.frames = frames.copy()
        del self.frames['Login']
        self.enroled = None
        self.roomtitle = None
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
            if msg.startswith(REQ_INVT + MSG_SEP):
                # do invitation
                msg = msg[2:]
                frame = self.frames['Lobby']
                # using another thread accept invitation
                t = threading.Thread(target=frame.raiseivt, args=(msg,))
                t.start()
            elif msg.startswith(REQ_PMSG + MSG_SEP):
                msg = msg[2:]
                frame = self.frames['PrivateChat']
                msginfo = msg.split(SPE_SEP)
                fromwho = msginfo[0]
                txt = msginfo[1]
                if self.privatechat is None:
                    a = tkMessageBox.askokcancel('New Message',
                                                 '%s send you a message: %s.\nDo you want to open?' % (fromwho, txt))
                    if a:
                        self.privatechat = fromwho
                        frame.prepare(txt, fromwho)
                else:
                    frame.updatelist(txt)
            elif msg.startswith(REQ_MSGS + MSG_SEP):
                # do msg notification
                msg = msg[2:]
                # update GUI
                frame = self.frames['Room']
                frame.msglist.insert(END, msg)
            else:
                for frame in self.frames.values():
                    frame.notification(msg)
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
                                   routing_key='rpc_queue',
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


"""---------------------------------------------------------------------------------------------------------------------
                                             Client GUI
---------------------------------------------------------------------------------------------------------------------"""


# **Main**---------------------------------------------------------------------------------------------------
class Client(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.title('Chat_Room')
        LOG.warn('Client has started!')
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (Login, Lobby, NewRoom, Room, PrivateChat):
            page_name = F.__name__
            frame = F(master=container, controller=self)
            self.frames[page_name] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")
        # create user instance
        self.user = User(self.frames)
        self.show_frame("Login")

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        frame = self.frames[page_name]
        frame.tkraise()


# **Login**---------------------------------------------------------------------------------------------------
class Login(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # 'Login' Frame
        self.login_frame = Frame(self, width=400, height=100, pady=75)
        self.login_frame.pack()
        # variables
        self.username = StringVar()
        # head label
        label = Label(self.login_frame, text='Enter your name to login', font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # name entry
        self.name_entry = Entry(self.login_frame, textvariable=self.username)
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        self.name_entry.focus()
        self.name_entry.bind('<Return>', self.connect)
        # submit button
        self.submit_button = Button(self.login_frame, text='Enter', command=self.connect)
        self.submit_button.grid(row=2, column=0, sticky=NSEW)
        self.quit_button = Button(self.login_frame, text='Quit', command=self.disconnect)
        self.quit_button.grid(row=2, column=1, sticky=NSEW)
        LOG.warn('Loading *Login* Page success!')

    def connect(self, e=None):
        name = self.name_entry.get()
        if name == '':
            tkMessageBox.showwarning('Input Error', 'Please input your name first!')
            return
        elif ':' in name:
            tkMessageBox.showwarning('Input Error', 'Plase don''t use '':''!')
            return
        elif '/' in name:
            tkMessageBox.showwarning('Input Error', 'Plase don''t use ''/''!')
            return
        rsp = self.controller.user.call(REQ_NAME, name)
        if rsp == RSP_OK:
            LOG.warn('Login to chat room!')
            # unbind key
            self.name_entry.unbind('<Return>')
            # set user name
            self.controller.user.name = name
            # update next frame
            frame = self.controller.frames['Lobby']
            frame.prepare()
            # show next frame
            self.controller.show_frame("Lobby")
        elif rsp == RSP_DUP:
            LOG.warn('Duplicated username!')
            tkMessageBox.showwarning('Login Failed', 'Your username already exists!')
            self.username.set('')
            self.name_entry.focus()
        else:
            LOG.warn('Unknown Error!')
            tkMessageBox.showwarning('Login Failed', 'Can''t login right now, please restart client!')
            self.username.set('')
            self.name_entry.focus()
        return

    def disconnect(self):
        self.controller.user.connection.close()
        self.quit()


# **Lobby**---------------------------------------------------------------------------------------------------
class Lobby(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('')
        # lobby frame
        self.lobby_frame = Frame(self, width=400, height=100, pady=10)
        self.lobby_frame.pack()
        # Slogan welcome
        label = Label(self.lobby_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=3, sticky=NSEW)
        # session table tree
        self.tree = ttk.Treeview(self.lobby_frame, selectmode='browse', show='headings', height=10, columns=('a', 'b'))
        self.tree.column('a', width=10, anchor='center')
        self.tree.column('b', width=50, anchor='center')
        self.tree.heading('a', text='Room ID')
        self.tree.heading('b', text='Title')
        self.tree.grid(row=1, column=0, columnspan=3, sticky=NSEW)
        # buttons
        self.select_button = Button(self.lobby_frame, text='Select', command=self.select)
        self.select_button.grid(row=2, column=0)
        self.create_button = Button(self.lobby_frame, text='Create new', command=self.create)
        self.create_button.grid(row=2, column=1)
        self.fetch_button = Button(self.lobby_frame, text='Quit', command=self.disconnect)
        self.fetch_button.grid(row=2, column=2)
        self.showuser_button = Button(self.lobby_frame, text='All Users', command=self.showuser)
        self.showuser_button.grid(row=3, column=0)
        self.primsg_button = Button(self.lobby_frame, text='Private Message', command=self.sendprivate, state=DISABLED)
        self.primsg_button.grid(row=3, column=1, columnspan=2, sticky=W)
        # place for notification
        self.notify_var = StringVar()
        self.notify_var.set('')
        self.noti_label = Label(self.lobby_frame, textvariable=self.notify_var)
        self.noti_label.grid(row=4, column=0, columnspan=3, sticky=NSEW)
        LOG.warn('Loading *Lobby* Page success!')

    def prepare(self):

        self.tree.bind('<Return>', self.select)
        self.welcome.set('Tere! %s' % self.controller.user.name)
        # fetch update
        self.fetch()
        return

    def select(self, e=None):
        # get room id
        item = self.tree.selection()[0]
        itemtup = self.tree.item(item, 'values')
        roomid = itemtup[0]
        # join room
        rsp = self.controller.user.call(REQ_JOIN, roomid)
        if rsp == RSP_OK:
            # unbind
            self.tree.unbind('<Return>')
            # set info
            self.controller.user.enrolled = roomid
            self.controller.user.roomtitle = itemtup[1]
            frame = self.controller.frames['Room']
            frame.prepare()
            self.controller.show_frame('Room')
        else:
            tkMessageBox.showwarning('Error occurred', 'Can''t join right now, please try later!')
        return

    def create(self):
        LOG.warn('Creating new room!')
        frame = self.controller.frames['NewRoom']
        frame.prepare()
        self.controller.show_frame('NewRoom')
        return

    def fetch(self):
        # delete old items
        for _ in map(self.tree.delete, self.tree.get_children('''''')):
            pass
        # get public room list
        rsp = self.controller.user.call(REQ_FECH, '')
        # update lobby (example:1/Beers:2/Chickens:3/Working-out!!:)
        splited_room = rsp.split(MSG_SEP)
        splited_room = splited_room[:-1]
        for room in splited_room:
            roominfo = room.split(DTA_SEP)
            self.tree.insert('', 'end', values=(roominfo[0], roominfo[1]))
        LOG.warn('Fetch room info complete!')
        return

    def showuser(self):
        # delete old items
        for _ in map(self.tree.delete, self.tree.get_children('''''')):
            pass
        self.tree.heading('a', text='Number')
        self.tree.heading('b', text='User')
        # get user list
        rsp = self.controller.user.call(REQ_USER, '')
        count = 1
        users = rsp.split(MSG_SEP)
        users = users[:-1]
        for user in users:
            self.tree.insert('', 'end', values=(str(count), user))
            count += 1
        LOG.warn('Fetch user info complete!')
        # change GUI
        self.select_button.config(state=DISABLED)
        self.showuser_button.config(text='All Rooms')
        self.showuser_button.config(command=self.showlobby)
        self.primsg_button.config(state='normal')

        return

    def showlobby(self):
        self.tree.heading('a', text='Room ID')
        self.tree.heading('b', text='Title')
        # get public rooms
        self.fetch()
        # change GUI
        self.select_button.config(state='normal')
        self.showuser_button.config(text='All Users')
        self.showuser_button.config(command=self.showuser)
        self.primsg_button.config(state=DISABLED)
        return

    def sendprivate(self):
        # get selected user
        item = self.tree.selection()[0]
        itemtup = self.tree.item(item, 'values')
        user = itemtup[1]
        # set private chat
        self.controller.user.privatechat = user
        # prepare frame
        frame = self.controller.frames['PrivateChat']
        frame.prepare(msg=None, title=user)
        return

    def notification(self, msg=None):
        if msg is None:
            self.notify_var.set('')
        else:
            self.notify_var.set(msg)
        # refresh notification every 15s
        self.noti_label.after(15000, self.notification)
        return

    def raiseivt(self, roominfo):
        roominfolist = roominfo.split(MSG_SEP)
        a = tkMessageBox.askokcancel('Invitation', 'Do you want to accept invitation?')
        if a:
            rsp = self.controller.user.call(REQ_JOIN, roominfolist[0])
            if rsp == RSP_OK:
                self.controller.user.enrolled = roominfolist[0]
                self.controller.user.roomtitle = roominfolist[1]
                frame = self.controller.frames['Room']
                frame.prepare()
                self.controller.show_frame('Room')
            else:
                tkMessageBox.showwarning('Error occurred', 'Can''t join right now, please try later!')
        return

    def disconnect(self):
        rsp = self.controller.user.call(REQ_QUIT, self.controller.user.name)
        if rsp.startswith(RSP_OK):
            self.controller.user.connection.close()
            self.quit()
        else:
            tkMessageBox.showwarning('Error occurred', 'Can''t quit right now, please try later!')
        return


# **NewRoom**---------------------------------------------------------------------------------------------------
class NewRoom(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('Create your Chat Room')
        # lobby frame
        self.newroom_frame = Frame(self, width=400, height=100, pady=10)
        self.newroom_frame.pack()
        # Slogan welcome
        label = Label(self.newroom_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # label
        self.name_label = Label(self.newroom_frame, text='Your room name:')
        self.name_label.grid(row=1, column=0)
        self.visible_label = Label(self.newroom_frame, text='Public/Private:')
        self.visible_label.grid(row=2, column=0)
        self.invite_label = Label(self.newroom_frame, text='Invite users:')
        self.invite_label.grid(row=3, column=0)
        # name entry
        self.name_var = StringVar()
        self.limit_entry = Entry(self.newroom_frame, textvariable=self.name_var)
        self.limit_entry.grid(row=1, column=1)
        # option menu
        OPTION = ['Public', 'Private']
        self.option_var = StringVar()
        self.option_menu = OptionMenu(self.newroom_frame, self.option_var, *OPTION)
        self.option_menu.grid(row=2, column=1, sticky=NSEW)
        # invite users menu
        self.listframe = Frame(self.newroom_frame)
        self.listframe.grid(row=3, column=1)
        self.userlist = Listbox(self.listframe, height=5, selectmode=MULTIPLE)
        self.userlist.grid(row=0, column=0)
        # add scroll bar
        self.scrollbar = Scrollbar(self.listframe, orient="vertical")
        self.scrollbar.config(command=self.userlist.yview)
        self.scrollbar.grid(row=0, column=1)
        self.userlist.config(yscrollcommand=self.scrollbar.set)
        # buttons
        self.submit_button = Button(self.newroom_frame, text='Submit', command=self.create_room)
        self.submit_button.grid(row=4, column=1, sticky=NSEW)
        self.back_button = Button(self.newroom_frame, text='Back', command=self.go_back)
        self.back_button.grid(row=4, column=0, sticky=NSEW)
        # place for notification
        self.notify_var = StringVar()
        self.notify_var.set('')
        self.noti_label = Label(self.newroom_frame, textvariable=self.notify_var)
        self.noti_label.grid(row=5, column=0, columnspan=2, sticky=NSEW)
        LOG.warn('Loading *NewRoom* Page success!')

    def prepare(self):
        # clear list box & entry
        self.userlist.delete(0, END)
        self.name_var.set('')
        # fetch all users
        rsp = self.controller.user.call(REQ_USER, '')
        count = 1
        users = rsp.split(MSG_SEP)
        users = users[:-1]
        for user in users:
            if user == self.controller.user.name:
                pass
            else:
                self.userlist.insert(END, user)
        return

    def go_back(self):
        LOG.warn('Back to Lobby.')
        self.controller.show_frame("Lobby")
        return

    def create_room(self):
        # get input
        roomname = self.name_var.get()
        openess = self.option_var.get()
        if openess == '':
            tkMessageBox.showwarning('Error occurred', 'Please specify your room property!')
            return
        elif roomname == '':
            tkMessageBox.showwarning('Error occurred', 'Please enter your room name!')
            return
        invitations = [self.userlist.get(idx) for idx in self.userlist.curselection()]
        msg = roomname + MSG_SEP + openess + MSG_SEP
        for person in invitations:
            msg = msg + person + DTA_SEP
        # create room
        rsp = self.controller.user.call(REQ_CRAT, msg)
        # set enrolled room id
        self.controller.user.enrolled = rsp
        self.controller.user.roomtitle = roomname
        frame = self.controller.frames['Room']
        frame.prepare()
        self.controller.show_frame('Room')
        return

    def notification(self, msg=None):
        if msg is None:
            self.notify_var.set('')
        else:
            self.notify_var.set(msg)
        # refresh notification every 15s
        self.noti_label.after(15000, self.notification)
        return


# **Room**---------------------------------------------------------------------------------------------------
class Room(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        # self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('')
        # lobby frame
        self.chatroom_frame = Frame(self, width=400, height=100, pady=10)
        self.chatroom_frame.pack()
        # Slogan welcome
        label = Label(self.chatroom_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=5, sticky=NSEW)
        # msg box
        self.msgframe = Frame(self.chatroom_frame)
        self.msgframe.grid(row=1, column=0, columnspan=5, sticky=NSEW)
        self.msglist = Listbox(self.msgframe, height=10)
        self.msglist.grid(row=0, column=0)
        # add scroll bar
        self.scrollbar = Scrollbar(self.msgframe, orient="vertical")
        self.scrollbar.config(command=self.msglist.yview)
        self.scrollbar.grid(row=0, column=1)
        self.msglist.config(yscrollcommand=self.scrollbar.set)
        # input entry
        self.input_var = StringVar()
        self.inputmsg = Entry(self.chatroom_frame, textvariable=self.input_var)
        self.inputmsg.grid(row=2, column=0, columnspan=5, sticky=NSEW)
        # buttons
        self.quit_button = Button(self.chatroom_frame, text='Quit', command=self.quitroom)
        self.quit_button.grid(row=3, column=0)
        self.users_button = Button(self.chatroom_frame, text='Users', command=self.listuser)
        self.users_button.grid(row=3, column=1)
        self.invite_button = Button(self.chatroom_frame, text='Invite', command=self.invite)
        self.invite_button.grid(row=3, column=2)
        self.send_button = Button(self.chatroom_frame, text='Send', command=self.sendmsg)
        self.send_button.grid(row=3, column=3)
        # place for notification
        self.notify_var = StringVar()
        self.notify_var.set('')
        self.noti_label = Label(self.chatroom_frame, textvariable=self.notify_var)
        self.noti_label.grid(row=4, column=0, columnspan=4, sticky=NSEW)
        LOG.warn('Loading *Room* Page success!')

    def sendmsg(self, e=None):
        # get entry
        msg = self.input_var.get()
        if msg == '':
            tkMessageBox.showwarning('No input', 'Please input something first!')
            return
        msg = self.controller.user.name + ': ' + msg
        # send msg
        rsp = self.controller.user.call(REQ_MSGS, msg)
        # update GUI
        self.msglist.insert(END, msg)
        self.input_var.set('')
        return

    def listuser(self):
        self.roomusers = Listbox(self.msgframe, height=10)
        self.roomusers.grid(row=0, column=0)
        # request for chat room users
        rsp = self.controller.user.call(REQ_RUSR, self.controller.user.enrolled)
        users = rsp.split(MSG_SEP)
        users = users[:-1]
        for user in users:
            self.roomusers.insert(END, user)
        # change GUI
        self.welcome.set('Room Users')
        self.users_button.config(text='MSG')
        self.users_button.config(command=self.listmsg)
        return

    def listmsg(self):
        self.roomusers.destroy()
        # change GUI
        self.welcome.set(self.controller.user.roomtitle)
        self.users_button.config(text='Users')
        self.users_button.config(command=self.listuser)
        return

    def listmsg2(self):
        self.inviteusers.destroy()
        # change GUI
        self.welcome.set(self.controller.user.roomtitle)
        self.invite_button.config(text='Invite')
        self.users_button.config(command=self.invite)
        self.send_button.config(text='Send')
        self.send_button.config(command=self.sendmsg)
        return

    def invite(self):
        self.inviteusers = Listbox(self.msgframe, height=10, selectmode=MULTIPLE)
        self.inviteusers.grid(row=0, column=0)
        # request for all users
        rsp = self.controller.user.call(REQ_USER, '')
        users = rsp.split(MSG_SEP)
        users = users[:-1]
        for user in users:
            if user == self.controller.user.name:
                pass
            else:
                self.inviteusers.insert(END, user)
        # change GUI
        self.welcome.set('Invite others to room')
        self.invite_button.config(text='MSG')
        self.invite_button.config(command=self.listmsg2)
        self.send_button.config(text='Invite')
        self.send_button.config(command=self.sendinvitation)
        return

    def sendinvitation(self):
        roomid = self.controller.user.enrolled
        msg = roomid + MSG_SEP
        # get selected user
        invitations = [self.inviteusers.get(idx) for idx in self.inviteusers.curselection()]
        if invitations == []:
            tkMessageBox.showwarning('No selection', 'Please select people you want to invite!')
            return
        for person in invitations:
            msg = msg + person + DTA_SEP
        # send invitation
        rsp = self.controller.user.call(REQ_INVT, msg)
        if rsp == RSP_OK:
            tkMessageBox.showwarning('Success', 'Your invitations have been sent!')
            self.listmsg2()
        else:
            tkMessageBox.showwarning('Failed', 'Error occurred!')
        return

    def prepare(self):
        # bind
        self.inputmsg.bind('<Return>', self.sendmsg)
        # clean msglist
        self.msglist.delete(0, END)
        # bind enter key
        self.send_button.bind('<Return>', self.sendmsg)
        # create room based on enrolled_id
        # title, userlist
        self.welcome.set(self.controller.user.roomtitle)
        return

    def notification(self, msg=None):
        if msg is None:
            self.notify_var.set('')
        else:
            self.notify_var.set(msg)
        # refresh notification every 15s
        self.noti_label.after(15000, self.notification)
        return

    def quitroom(self):
        # unbind
        self.inputmsg.unbind('<Return>')
        roomid = self.controller.user.enrolled
        rsp = self.controller.user.call(REQ_QROM, roomid)
        if rsp == RSP_OK:
            frame = self.controller.frames['Lobby']
            frame.prepare()
            self.controller.show_frame('Lobby')
        else:
            tkMessageBox.showwarning('Error occurred', 'Can''t quit right now, please try later!')
        return


# **PrivateChat**---------------------------------------------------------------------------------------------------
class PrivateChat(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        self.controller = controller
        # welcome string
        self.welcome = StringVar()
        self.welcome.set('')
        # lobby frame
        self.chatroom_frame = Frame(self, width=400, height=100, pady=10)
        self.chatroom_frame.pack()
        # Slogan welcome
        label = Label(self.chatroom_frame, textvariable=self.welcome, font=controller.title_font)
        label.grid(row=0, column=0, columnspan=5, sticky=NSEW)
        # msg box
        self.msgframe = Frame(self.chatroom_frame)
        self.msgframe.grid(row=1, column=0, columnspan=5, sticky=NSEW)
        self.msglist = Listbox(self.msgframe, height=10)
        self.msglist.grid(row=0, column=0)
        # add scroll bar
        self.scrollbar = Scrollbar(self.msgframe, orient="vertical")
        self.scrollbar.config(command=self.msglist.yview)
        self.scrollbar.grid(row=0, column=1)
        self.msglist.config(yscrollcommand=self.scrollbar.set)
        # input entry
        self.input_var = StringVar()
        self.inputmsg = Entry(self.chatroom_frame, textvariable=self.input_var)
        self.inputmsg.grid(row=2, column=0, columnspan=5, sticky=NSEW)
        # buttons
        self.quit_button = Button(self.chatroom_frame, text='Quit', command=self.quitroom)
        self.quit_button.grid(row=3, column=0, columnspan=2)
        self.send_button = Button(self.chatroom_frame, text='Send', command=self.sendmsg)
        self.send_button.grid(row=3, column=3, columnspan=2)
        # place for notification
        self.notify_var = StringVar()
        self.notify_var.set('')
        self.noti_label = Label(self.chatroom_frame, textvariable=self.notify_var)
        self.noti_label.grid(row=4, column=0, columnspan=4, sticky=NSEW)
        LOG.warn('Loading *PricateChat* Page success!')

    def prepare(self, msg=None, title=None):
        self.inputmsg.bind('<Return>', self.sendmsg)
        # clean UI
        self.welcome.set('')
        self.msglist.delete(0, END)
        # set UI
        self.welcome.set('Chat with %s' % title)
        # set msg
        self.msglist.insert(END, msg)
        # show frame
        self.controller.show_frame('PrivateChat')
        return

    def updatelist(self, msg):
        self.msglist.insert(END, msg)
        return

    def sendmsg(self, e=None):
        # get data
        msg = self.input_var.get()
        msg = self.controller.user.name + ': ' + msg
        # update GUI
        self.msglist.insert(END, msg)
        self.input_var.set('')
        # assemble MSG
        msg = self.controller.user.privatechat + SPE_SEP + msg
        # send
        rsp = self.controller.user.call(REQ_PMSG, msg)
        return

    def quitroom(self):
        self.inputmsg.unbind('<Return>')
        # clear chat
        self.controller.user.privatechat = None
        # clean UI
        self.welcome.set('')
        self.msglist.delete(0, END)
        # raise frame
        frame = self.controller.frames['Lobby']
        frame.prepare()
        self.controller.show_frame('Lobby')
        return

    def notification(self, msg=None):
        if msg is None:
            self.notify_var.set('')
        else:
            self.notify_var.set(msg)
        # refresh notification every 15s
        self.noti_label.after(15000, self.notification)
        return


"""---------------------------------------------------------------------------------------------------------------------
                                        Client Main Function

                                create client instance, run GUI in loop
---------------------------------------------------------------------------------------------------------------------"""
if __name__ == '__main__':
    app = Client()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        LOG.warn('User terminated client!')
