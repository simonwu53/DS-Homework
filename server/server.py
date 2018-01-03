import logging
import pika
import threading
from time import sleep
import sudoku_generator
import operator
from multicast_server import *

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
# multi-cast
MULTICAST_PERIOD = 10


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
        result = self.channel.queue_declare(exclusive=True)
        self.server_q = result.method.queue
        # process 1 task each time
        self.channel.basic_qos(prefetch_count=1)
        # set consume
        self.channel.basic_consume(self.on_request, queue=self.server_q, no_ack=True)
        # start multi-casting
        mc_ip, mc_port = '239.1.1.1', 7778
        self.multicast = threading.Thread(target=self.multicasting, args=(mc_ip, mc_port))
        self.multicast.daemon = True
        self.multicast.start()
        LOG.warn('Awaiting RPC requests')

    def noti_queues(self,gameid,name):
        oldtarget = []
        for user in self.gameinfo[gameid]:
            oldtarget.append(user)
        #oldtarget = (self.gameinfo[gameid]).copy()    #else somebody left, let's notify them !!!
        oldtarget.remove(name)   # line 144 already removed user... and this target is not right
        target=[]
        for key in self.users:
            for people in oldtarget:
                if key==people:
                    target.append(self.users[key])
        return target            

    
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
            self.id += 1  # game ids will start from 1
            str_id = str(self.id)
            sudoku_answer, generated_sudoku = sudoku_generator.setup_sudoku(difficulty)
            sudoku.append(generated_sudoku)
            sudoku.append(limit)
            names.append(username)
            self.game[self.id] = sudoku
            self.gameinfo[self.id]=names
            self.answers[self.id] = sudoku_answer
            print(sudoku_answer)
            score[username] = 0 # saving score 
            self.rooms[self.id] = score
            rsp = CTR_RSP +  MSG_SEP+ str_id
            
        # REQ 2--------------------------------------------------------------------------------
        elif body.startswith(REQ_QUIT+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_QUIT)
            body = body[2:]
            msg=body.split(MSG_SEP)
            game_id=int(msg[0])
            name=msg[1]
            noti_msg = ''
            rsp=''
            if msg[0]=="0":
                del self.users[name]
                rsp = CTR_RSP + MSG_SEP + RSP_OK
            else:
                target = self.noti_queues(game_id, name)
                del self.rooms[game_id][name]
                self.gameinfo[game_id].remove(name)
                if len(self.rooms[game_id]) == 0: #if no user left to the game session delete it,send rsp ok
                    del self.rooms[game_id]
                    del self.game[game_id]
                    del self.answers[game_id]
                    del self.gameinfo[game_id] 
                    rsp = CTR_RSP +  MSG_SEP+ RSP_OK
                    target = None
                else:
                    
                    rsp = CTR_RSP +  MSG_SEP+ RSP_OK
                    if target == []:
                        target = None
                    else:
                        noti_msg = CTR_NOT+MSG_SEP+NOTI_QUIT+MSG_SEP+name
            
            LOG.warn('User %s has quit!' % name)
        elif body.startswith(REQ_JOIN+MSG_SEP):
            LOG.warn('REQ code: %s' % REQ_JOIN)
            body = body[2:]
            msg=body.split(MSG_SEP)
            game_id=int(msg[0])
            name=msg[1]
            noti_msg = ''
            rsp=''
            if len(self.rooms[game_id]) > self.game[game_id][1]:
                rsp=CTR_RSP + MSG_SEP + RSP_ERR   # limit is already reached at this game session
                LOG.warn("limit reached")
            else:
                self.rooms[game_id][name] = 0  # otherwise user is registered to the wanted game session and started from the score 0.
                self.gameinfo[game_id].append(name)
                # notification
                LOG.warn("new user joined")
                rsp= CTR_RSP + MSG_SEP + RSP_OK
                target=self.noti_queues(game_id,name)
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
            for user_name in self.rooms[game_id]:  
                msg +=  user_name + DTA_SEP + str(self.rooms[game_id][user_name]) + MSG_SEP #header:username/score:username/score

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
            msg = ''
            rsp=''
            for key in self.game:
                numb_players = str(len(self.rooms[key]))
                msg += str(key) + DTA_SEP + numb_players + DTA_SEP +  self.game[key][1] 
                msg += MSG_SEP
            rsp=CTR_RSP + MSG_SEP + msg
          # 1:1/5/4:   this kind of string will be returned. header:gameid/players/limit
        # REQ move-------------------------------------------------------------------------------
        elif body.startswith(REQ_MOVE + MSG_SEP):
            msg = body[2:]
            split_msg = msg.split(MSG_SEP)
            gid = int(split_msg[0])
            sudoku = self.game[gid][0]
            position = int(split_msg[1])
            number = split_msg[2]
            player = split_msg[3]
            if sudoku[position] =='_': # if position is free    
                correct_number = self.answers[gid][position] #find correct number in the sudoku answers    
                if number == correct_number:  #if the number is correct
                    x = self.rooms[gid][player] #find the user's previous score
                    x += 1  #increase by one
                   # str(x) #make it string and update the score
                    self.rooms[gid][player] = x
                    logging.debug("correct move")
                    sudoku[position] = number #put the new number in the sudoku
                    rsp = CTR_RSP + MSG_SEP + RSP_OK
                    if self.answers[gid] == self.game[gid][0]: # check if sudoku is full and notify the winner and users
                        user_dict = self.rooms[gid]
                        winner_user = max(user_dict.iteritems(), key=operator.itemgetter(1))[0]  
                        winner_score=max(user_dict.values())                        
                        target=self.noti_queues(gid,player)
                        if target == []:
                            target = None
                        else:
                            noti_msg = CTR_NOT + MSG_SEP + NOTI_WINNER + MSG_SEP + winner_user + MSG_SEP + str(winner_score)
                    else: # Game not finished notify the users about changed scores and sudoku
                        target=self.noti_queues(gid,player)
                        if target == []:
                            target = None
                        else:
                            noti_msg = CTR_NOT + MSG_SEP + NOTI_MOVE + MSG_SEP
                else: #wrong move , decrease the score of the user and update the scores, notify the users about changes
                    x = int(self.rooms[gid][player])
                    x -= 1
                    #str(x)
                    self.rooms[gid][player] = x
                    logging.debug("wrong move")
                    rsp = CTR_RSP + MSG_SEP + RSP_ERR
                    target=self.noti_queues(gid,player)
                    if target == []:
                        target = None
                    else:
                        noti_msg = CTR_NOT + MSG_SEP + NOTI_MOVE 
            else: #late move
                logging.debug("late move")
                rsp = CTR_RSP + MSG_SEP + RSP_LATE
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
        # msg = CTR_NOT + MSG_SEP + m
        for queue in des:
            ch.basic_publish(exchange='',
                             routing_key=queue,
                             body=m)
            # ch.basic_ack(delivery_tag=method.delivery_tag)
        LOG.warn('Notification sent!')
        return

    def multicasting(self, mc_ip, mc_port):
        while True:
            send_whoishere(self.server_q, (mc_ip, mc_port))
            sleep(MULTICAST_PERIOD)

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
