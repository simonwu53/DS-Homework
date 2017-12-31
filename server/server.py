import logging
import pika
import threading
from time import sleep
import sudoku_generator
import operator
"""---------------------------------------------------------------------------------------------------------------------
                                            LOG info
---------------------------------------------------------------------------------------------------------------------"""
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.WARN, format=FORMAT)
LOG = logging.getLogger()
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
CTR_NOT = '0'   #controle code about notification
CTR_RSP = '1'   #controle code about response
# server response
RSP_ERR = '0'
RSP_OK = '1'  
RSP_DUP = '2'   #such name already exists!
RSP_LATE = '3'
# client code
REQ_NAME = '0'  # register new user
REQ_CREATE = '1'    #user wants to create new game
REQ_JOIN = '2'   #user wants to join existing game
REQ_MOVE = '3'    #user wants to move
REQ_QUIT = '4'  # client send: `Header:gameid:username`
                # server reply: `CTR_RSP:RSP_OK` notify others: `CTR_NOT:NOTI_QUIT:name`
                #user wants to quit
REQ_getRoom = '5'  #geting game session
REQ_getSudoku = '6'   #fetch sudoku !
REQ_getUser = '7'   #get user info like: username/score:username/score
# notifications
NOTI_JOIN = '0'    #notificate user about joining new person
NOTI_MOVE = '1'    #notify about move
NOTI_QUIT = '2'    #notify somebody quitted
NOTI_WINNER = '3'   #announce the winner


"""---------------------------------------------------------------------------------------------------------------------
                                            Server Class
---------------------------------------------------------------------------------------------------------------------"""


class Server:
    def __init__(self):

        self.users = {}  # username:queue
        self.rooms = {}  # {game_id:{username:score}}
        #self.score={} #here username and score will be stored {username:score}
        self.id=0 # game id , it will be increased as new games are created one by one
        self.answers={}  # {game_id:sudoku_answ}
        self.game={} #  {game id: [[sudoku_game], limit]}
        self.gameinfo={}  #gameid:[list of people]
        # connect to broker
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1')) 
        # declare channel
        self.channel = self.connection.channel()
        # declare server queue
        self.channel.queue_declare(queue='')  
        # process 1 task each time
        self.channel.basic_qos(prefetch_count=1)
        # set consume
        self.channel.basic_consume(self.on_request, queue='', no_ack=True)
        LOG.warn('Awaiting RPC requests')

    def on_request(self, ch, method, props, body):
        target = None
        # REQ 0--------------------------------------------------------------------------------
        if body.startswith(REQ_NAME + MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_NAME)
            body = body[2:]
            if self.users.has_key(body):
                LOG.warn('Duplicated name.')
                rsp = CTR_RSP + MSG_SEP + RSP_DUP
            else:
                rsp = CTR_RSP + MSG_SEP + RSP_OK
                # register user
                self.users[body] = props.reply_to
                LOG.warn('Name valid, registered to database.')
        
        # REQ 1--------------------------------------------------------------------------------
        elif body.startswith(REQ_CREATE + MSG_SEP):
            sudoku=[]
            score={}
            names=[]
            LOG.warn('REQ code: %s' % REQ_CREATE)
            rsp = ''
            body = body[2:]
            msg=body.split(MSG_SEP)
            difficulty=msg[0]
            limit=msg[1]
            username=msg[2]
            id += 1  # game ids will start from 1
            str_id = str(id)
            sudoku_answer, generated_sudoku = sudoku_generator.setup_sudoku(difficulty)
            sudoku.append(generated_sudoku)
            sudoku.append(limit)
            names.append(username)
            self.game[id] = sudoku
            self.gameinfo[id]=names
            self.answers[id] = sudoku_answer
            score[username] = 0 # saving score 
            self.room[id] = self.score
            rsp = CTR_RSP +  MSG_SEP+ str_id
            
        # REQ 2--------------------------------------------------------------------------------
        elif body.startswith(REQ_QUIT+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_QUIT)
            body = body[2:]
            msg=body.split(MSG_SEP)
            game_id=int(msg[0])
            name=msg[1]
            noti_msg = ''
            del self.rooms[game_id][name]
            if len(self.rooms[game_id]) == 0: #if no user left to the game session delete it,send rsp ok
                del self.rooms[game_id]
                del self.game[game_id]
                del self.answers[game_id]
                del self.gameinfo[game_id] 
                rsp = CTR_RSP +  MSG_SEP+ RSP_OK
            else:
                target = self.gameinfo[game_id]       #else somebody left, let's notify them !!!
                target.remove(name)
                rsp = CTR_RSP +  MSG_SEP+ RSP_OK
                if target == []:
                    target = None
                else:
                    noti_msg = CTR_NOT+MSG_SEP+NOTI_QUIT+MSG_SEP+name
            
                    LOG.warn('User %s has quit!' % body)
        elif body.startswith(REQ_JOIN+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_JOIN)
            body = body[2:]
            msg=body.split(MSG_SEP)
            game_id=int(msg[0])
            name=msg[1]
            noti_msg = ''
            rsp=''
            if (len(self.rooms[game_id]) > self.game[game_id][1]):
                rsp=CTR_RSP + MSG_SEP + RSP_ERR   # limit is already reached at this game session
                LOG.warn("limit reached")
            self.rooms[game_id][name] = 0 # otherwise user is registered to the wanted game session and started from the score 0.
            self.gameinfo[game_id].append(name)
            #notification
            LOG.warn("new user joined")
            rsp= CTR_RSP + MSG_SEP + RSP_OK
            target = self.gameinfo[game_id]
            target.remove(name)
            if target == []:
                target = None
            else:
                noti_msg = CTR_NOT + MSG_SEP + NOTI_JOIN + MSG_SEP + name
                LOG.warn("notification to users sent")
            
        # REQ 3--------------------------------------------------------------------------------
        elif body.startswith(REQ_getUser +MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_getUser )
            rsp = ''
            msg=''
            body = body[2:]
            msgi=body.split(MSG_SEP)
            game_id=int(msgi[0])
            for user_name in self.roots[game_id]:  
                msg +=  user_name + DTA_SEP + str(self.roots[game_id][user_name][0]) + MSG_SEP #header:username/score:username/score

            rsp = CTR_RSP + MSG_SEP + msg
            LOG.warn("user infos sent to server")
        # REQ 4--------------------------------------------------------------------------------
        elif body.startswith(REQ_getSudoku+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_getSudoku)
            body = body[2:]
            rsp = ''
            msgi=body.split(MSG_SEP)
            game_id=int(msgi[0])    #getting send game id 
            sudokuu=self.game[game_id][0]
            rsp=CTR_RSP + MSG_SEP +''.join(sudokuu)   #sudoku is fetched and sent
            LOG.warn("sudoku sent to server")
            
     # REQ 5--------------------------------------------------------------------------------
        elif body.startswith(REQ_getRoom+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_getRoom)
          
        # REQ 6--------------------------------------------------------------------------------
        elif body.startswith(REQ_JOIN+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_JOIN)
            body = body[2:]
            target = []
            username = self.users.keys()[self.users.values().index(props.reply_to)]
            # check if he is from an invitation and already in a room
            for values in self.rooms.values():
                if username in values:
                    # get room id
                    roomid = self.rooms.keys()[self.rooms.values().index(values)]
                    # quit the room
                    values.remove(username)
                    if values == []:
                        LOG.warn('No one in the room, clean the room...')
                        del self.rooms[roomid]
                        if roomid.startswith('p'):
                            del self.lobby[roomid]
                        elif roomid.startswith('h'):
                            del self.hidden_lobby[roomid]
            # find room
            userlist = self.rooms[body]
            # prepare notification
            for user in userlist:
                target.append(self.users[user])
            noti_msg = '%s has joined the chat room!' % username
            # join room
            userlist.append(username)
            rsp = CTR_RSP + MSG_SEP + RSP_OK
        # REQ 7--------------------------------------------------------------------------------
        elif body.startswith(REQ_QROM+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_QROM)
            roomid = body[2:]
            username = self.users.keys()[self.users.values().index(props.reply_to)]
            # delete user from room
            userlist = self.rooms[roomid]
            userlist.remove(username)
            self.rooms[roomid] = userlist
            LOG.warn('%s has quit the room.' % username)
            if userlist == []:
                LOG.warn('No one in the room, clean the room...')
                del self.rooms[roomid]
                if roomid.startswith('p'):
                    del self.lobby[roomid]
                elif roomid.startswith('h'):
                    del self.hidden_lobby[roomid]
            else:
                # there is people, notify leaving
                target = []
                for user in userlist:
                    target.append(self.users[user])
                noti_msg = '%s has left the chat room!' % username
            rsp = CTR_RSP + MSG_SEP + RSP_OK
        # REQ 8--------------------------------------------------------------------------------
        elif body.startswith(REQ_RUSR+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_RUSR)
            roomid = body[2:]
            # get room users
            userlist = self.rooms[roomid]
            rsp = ''
            for user in userlist:
                rsp = rsp + user + MSG_SEP
            rsp = CTR_RSP + MSG_SEP + rsp
        # REQ 9--------------------------------------------------------------------------------
        elif body.startswith(REQ_MSGS+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_MSGS)
            msg = body[2:]
            users = None
            target = []
            username = self.users.keys()[self.users.values().index(props.reply_to)]
            for userlist in self.rooms.values():
                if username in userlist:
                    users = list(userlist)
            users.remove(username)
            for user in users:
                target.append(self.users[user])
            # if no others, don't send notification
            if target == []:
                target = None
            else:
                # add header for notification
                noti_msg = REQ_MSGS + MSG_SEP + msg
            # send rsp
            rsp = CTR_RSP + MSG_SEP + RSP_OK
        # REQ 10-------------------------------------------------------------------------------
        elif body.startswith(REQ_PMSG+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_PMSG)
            msg = body[2:]
            # get from where
            username = self.users.keys()[self.users.values().index(props.reply_to)]
            # get to where
            msginfo = msg.split(SPE_SEP)
            towhom = msginfo[0]
            # prepare notification
            target = [self.users[towhom]]
            # assemble new msg
            newmsg = username + SPE_SEP + msginfo[1]
            # send notification
            noti_msg = REQ_PMSG + MSG_SEP + newmsg
            rsp = CTR_RSP + MSG_SEP + RSP_OK
        # REQ 11-------------------------------------------------------------------------------
        elif body.startswith(REQ_MOVE + MSG_SEP):
            msg = body[2:]
            split_msg = msg.split(DTA_SEP)
            gid = int(split_msg[0])
            sudoku = self.game[gid][0]
            position = int(split_msg[2])
            number = split_msg[3]
            player = split_msg[1]
            if sudoku[position] =='_': # if position is free
    
                correct_number = self.answers[gid][position] #find correct number in the sudoku answers
    
                if number == correct_number:  #if the number is correct
                    x = self.rooms[gid][player][0] #find the user's previous score
                    x += 1  #increase by one
                    str(x) #make it string and update the score
                    self.rooms[gid][player][0] = x
                    logging.debug("correct move")
                    sudoku[position] = number #put the new number in the sudoku
                    if self.answers[gid] == self.game[gid][0]: # check if sudoku is full and notify the winner and users
                        user_dict   = self.rooms[gid]
                        winner_user = max(user_dict.iteritems(), key=operator.itemgetter(1))[0]                       
                        #assemble the message
                        message = winner_user + DTA_SEP + str(user_dict[winner_user][0])
                        """
                        message=winner(gid)
                        t = Thread(target=notification_thread, args=(message, gid))
                        return __RSP_OK,t,None
                    else: # Game not finished notify the users about changed scores and sudoku
                        message=notify(gid)
                        t = Thread(target=notification_thread, args=(message, gid))
                        message1=sudoku1(gid)
                        t1=Thread(target=notification_thread, args=(message1, gid))
                        return __RSP_OK, t, t1
                        """
                else: #wrong move , decrease the score of the user and update the scores, notify the users about changes
                    x = int(user[gid][player][0])
                    x -= 1
                    str(x)
                    self.rooms[gid][player][0] = x
                    logging.debug("wrong move")
                    #message = notify(gid)
                    #t = Thread(target=notification_thread, args=(message, gid))
                    return 
            else: #late move
                logging.debug("late move")
                return 
        # UNKNOW REQ---------------------------------------------------------------------------
        else:
            rsp = CTR_RSP + MSG_SEP + RSP_ERR
        # send rsp-----------------------------------------------------------------------------
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=rsp)
        # ch.basic_ack(delivery_tag=method.delivery_tag)
        LOG.warn('Reply sent!')
        sleep(1)
        if target is None:
            pass
        else:
            self.send_noti(target, noti_msg, ch, method)


    def start_consume(self):
        # start listening
        self.channel.start_consuming()
        LOG.warn('Starting consuming')
        return

    def send_noti(self, des, m, ch, method):
        msg = CTR_NOT + MSG_SEP + m
        for queue in des:
            ch.basic_publish(exchange='',
                             routing_key=queue,
                             body=msg)
            # ch.basic_ack(delivery_tag=method.delivery_tag)
        LOG.warn('Notification sent!')
        return

    def on_close(self):
        self.connection.close()
        return

"""---------------------------------------------------------------------------------------------------------------------
                                        Server Main Function

                                create server instance, consume forever
---------------------------------------------------------------------------------------------------------------------"""
s = Server()
try:
    s.start_consume()
except KeyboardInterrupt:
    LOG.warn('Ctrl+C issued!')
    s.on_close()
    LOG.warn('Bye:)')
