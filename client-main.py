from Tkinter import *
import tkMessageBox
import tkFont as tkfont
import ttk
import re
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(threadName)-2s) %(message)s',)


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

        self.frames = {}
        for F in (Login, Waiting):
            page_name = F.__name__
            frame = F(master=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Login")

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
        self.score = IntVar()
        self.name_entry = StringVar()
        """login page"""
        logging.debug('Waiting for input username')
        # login frame
        self.login_frame = Frame(self, width=300, height=150)
        self.login_frame.pack()
        # input label
        self.login_name_label = Label(self.login_frame, text='Please input your user name:')
        self.login_name_label.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        # username entry
        self.login_name_entry = Entry(self.login_frame, textvariable=self.name_entry)
        self.login_name_entry.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        # submit button
        self.login_submit_button = Button(self.login_frame, text='Submit', command=self.check_username)
        self.login_submit_button.grid(row=1, column=2, sticky=W)
        self.login_quit_button = Button(self.login_frame, text='Quit', command=self.quit)
        self.login_quit_button.grid(row=1, column=2, sticky=E)
        # foot label
        self.login_foot_label = Label(self.login_frame, text='No more than 8 characters. No special symbols.')
        self.login_foot_label.grid(row=2, column=0, columnspan=3, sticky=NSEW)

    def check_username(self):
        # get input name
        self.name = self.login_name_entry.get()
        logging.debug('Checking username')
        try:
            check = re.search('\w+', self.name, flags=0).group()
            if check == str(self.name):
                logging.debug('Player name set to %s!' % self.name)
                tkMessageBox.showinfo('Welcome', 'Welcome to Sudoku game! %s' % self.name)
                self.controller.show_frame("Waiting")
            else:
                logging.debug('Name Error: Illegal username!')
                tkMessageBox.showwarning('Name Error', 'Illegal username!')
                self.name_entry.set('')
        except AttributeError:
            logging.debug('Name Error: No character input!')
            tkMessageBox.showwarning('Name Error', 'No character input!')
            self.name_entry.set('')



    def return_info(self):
        return self.name


class Waiting(Frame):
    def __init__(self, master, controller):
        # init Frame
        Frame.__init__(self, master)
        self.pack(side="top", fill="both", expand=True)
        # get info from server
        self.name = StringVar()
        self.name.set('Welcome: Shan!')

        """Waiting page"""
        label = Label(self, textvariable=self.name, font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)


if __name__ == '__main__':
    app = Client()
    app.mainloop()
