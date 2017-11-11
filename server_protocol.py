import logging
import time
import numpy as np
import sudoku_generator
import operator

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

# Protocol Recv Size ---------------------------------------------------------
#TCP_RECEIVE_BUFFER_SIZE=1024*1024
#MAX_PDU_SIZE = 200*1024*1024
# dictionaries
game = {}
MSG_SEP = ':'
DATA_SEP= '/'
user_names={} #here are stored all the usernames
score={} #here username and score will be stored
sudoku = [] #here will be stored sudoku and player limits
user={} #this dictionary contains game_id as key which correspondes to the players with their scores
id=0 # game id , it will be increased as new games are created one by one
#sudoku_generator=[]
sudoku_answer={}
# Requests --------------------------------------------------------------------
# Requests --------------------------------------------------------------------
# client requests
__REQ_REG = '1'
__REQ_JOIN = '2'
__REQ_MOVE = '3'
__REQ_QUIT = '4'
__REQ_SUDOKU = '5'
__REQ_USER = '6'
# server requests(notify)
__REQ_STARTGAME = '7'
__REQ_WINNER = '8'
__REQ_NOTIFY = '9'
__CTR_MSGS = {__REQ_REG: 'Register user name in server', # client recv OK or ___
              __REQ_MOVE: 'Player suggest one attempt', # client recv OK or ___
              __REQ_JOIN: 'Request to join game session', # client recv OK or ___
              __REQ_QUIT: 'Player leave game session', # client recv can be none
              __REQ_SUDOKU: 'Fetch the sudoku & player limit',
              __REQ_USER: 'Fetch the user name & scores in sudoku',
              # ---------------------------------------------
              __REQ_STARTGAME: 'Server start the game', # client recv can be none
              __REQ_WINNER: 'Game end claim winner',  # client recv winner name
              __REQ_NOTIFY: 'Notify player changes' # include someone leave -> client recv new scores
              }

# Responses--------------------------------------------------------------------
__RSP_OK = '0' # client also use OK rsp
__RSP_BADFORMAT = '1' # client also use
__RSP_UNKNCONTROL = '2' # client also use
__RSP_DUPNAME = '3'
__RSP_JOINFAIL = '4'
__RSP_WRONGMOVE = '5'
__RSP_LATEMOVE = '6',
__RSP_ERRTRANSM = '7'
__ERR_MSGS = {__RSP_OK: 'No Error',
              __RSP_BADFORMAT: 'Unknown message',
              __RSP_UNKNCONTROL: 'Unknown header',
              __RSP_DUPNAME: 'Duplicated name',
              __RSP_JOINFAIL: 'Fail to join game session',
              __RSP_WRONGMOVE: 'Player suggest wrong answer, -1 score',
              __RSP_LATEMOVE: 'Player''s move was late',
              __RSP_ERRTRANSM: 'Socket send&recv error'
              }

def startgame():
    
    #assemble the message
    message = __REQ_STARTGAME + MSG_SEP
    
    return message

def winner(gameid):

    #find the winner 
    user_dict   = user[gameid]
    winner_user = max(user_dict.iteritems(), key=operator.itemgetter(1))[0]
    
    #assemble the message
    message = __REQ_WINNER + MSG_SEP + winner_user + DATA_SEP + str(user[winner_user][0]) 
    
    return message
    
    
def notify(gameid):
    
    #get user:score data
    user_score_dict = user[gameid]
    user_score_list = user_score_dict.items()

    #assemble the message
    for i in range(len(user_score_dict)-1):
        user_score_string = user_score_list[i][0] + DATA_SEP + user_score_list[i][1] + MSG_SEP
        
    message = __REQ_NOTIFY + MSG_SEP + user_score_string
    
    return message
    
    
def sudoku(gameid):
    
    #get sudoku
    sudoku = game[gameid][0]
    
    #assemble the message
    message = __REQ_SUDOKU + MSG_SEP + sudoku    
    
    return message
    
def server_process(message,client_socket,server_socket):
    '''Process the client's message,
        @param message: string, protocol data unit received from client
                @returns string, response to send to client
    '''
    LOG.debug('Received request [%d bytes] in total' % len(message))
    if len(message) < 2:
        LOG.degug('Not enough data received from %s ' % message)
        return __RSP_BADFORMAT
    LOG.debug('Request control code (%s)' % message[0])
    if message.startswith(__REQ_REG + MSG_SEP):
        msg = message[2:]
        if msg in user_names:
            return __RSP_DUPNAME
        else:
            user_names.append(msg)
            return __RSP_OK
    if message.startswith(__REQ_JOIN + MSG_SEP): #here is 2 step a) user wants to join existing game or b)creating new game
        msg=message[2:]
        split_msg=msg.split(DATA_SEP)
        var=split_msg[0]
        if var.isdigit():
             #if user wants to join existing game
            name=split_msg[1]
            game_id=int(var)
            if(len(user[game_id])>game[game_id][1]):
                return __RSP_JOINFAIL # limit is already reached at this game session
            user[game_id][name] =0 #otherwise user is registered to the wanted game session and started from the score 0.
            return __RSP_OK
        else:# else user wants to create new session
            name = split_msg[0]
            limit = split_msg[1]
            difficulty = split_msg[2]
            id+=1 # game ides will start from 1
            str_id=str(id)
            sudoku_answer, generated_sudoku=sudoku_generator.setup_sudoku(difficulty)
            sudoku.append(generated_sudoku)
            sudoku.append(limit)
            game[id]=sudoku
            answers[id]=sudoku_answer
            score[name] = [0, client_socket]  # add user 1
            User[id] = score
            return MSG_SEP.join((__RSP_OK,)+tuple(str_id))
    if message.startswith(REQ_SUDOKU + MSG_SEP):
        msg = ''
        for key in game:
            numb_players=str(len(user[key]))
            msg+=str(key)+DATA_SEP+''.join(game[key][0])+DATA_SEP+game[key][1]+DATA_SEP+numb_players
        msg += MSG_SEP
        return __RSP_OK+ MSG_SEP+msg

    if message.startswith(__REQ_USER + MSG_SEP):
        msg = ''
        for key in user:
            msg += str(key)
            for user_name in User[key]:  # will be returned in request_user
                msg += DATA_SEP + user_name + DATA_SEP + str(User[key][user_name])
        msg += MSG_SEP
        return __RSP_OK + MSG_SEP + msg

    if message.startswith(__REQ_QUIT + MSG_SEP):
        msg = message[2:]
        split_msg = msg.split(DATA_SEP)
        user_name=split_msg[1]
        game_id=split_msg[0]
        del user[game_id][user_name]
        del user[game_id][user_name][1]
        # msg =req_notify
        # thread=(targer='')
        if len(user[game_id]) == 0:
            del user[game_id]
            del game[game_id]
            del sudoku_answer[game_id]
        if split_msg[2]=='close':
            return 'close'


        return __RSP_OK














    elif message.startswith(__REQ_LAST + __MSG_FIELD_SEP):
        s = message[2:]
        try:
            n = int(s)
            LOG.debug('New message listing request from %s:%d, '\
                      'messages %d' % (source+(n,)))
        except ValueError:
            LOG.debug('Integer required, %s received' % s)
            return __RSP_BADFORMAT
        ids = board.last(n)
        LOG.debug('Last %d ids: %s ' % (n,','.join(map(str,ids))))
        return __MSG_FIELD_SEP.join((__RSP_OK,)+tuple(map(str,ids)))
    elif message.startswith(__REQ_GET + __MSG_FIELD_SEP):
        s = message[2:]
        try:
            m_id = int(s)
            LOG.debug('New message request by id from %s:%d, '\
                      'id %d' % (source+(m_id,)))
        except ValueError:
            LOG.debug('Integer required, %s received' % s)
            return __RSP_BADFORMAT
        m = board.get(m_id)
        if m == None:
            LOG.debug('No messages by iD: %d' % m_id)
            return __RSP_MSGNOTFOUND
        m = map(str,m)
        return __MSG_FIELD_SEP.join((__RSP_OK,)+tuple(m))
    elif message.startswith(__REQ_GET_N_LAST + __MSG_FIELD_SEP):
        s = message[2:]
        try:
            n = int(s)
            LOG.debug('Client %s:%d requests %s last'\
                      'messages' % (source+('all' if n <= 0 else '%d' % n,)))
        except ValueError:
            LOG.debug('Integer required, %s received' % s)
            return __RSP_BADFORMAT
        # Get last N ids
        ids = board.last(n)
        # Get messages by ids
        msgs = map(board.get,ids)
        # Turn everything to string, use space to separate message meta-info
        #  [ "<timestamp> <ip> <port> <message>", ... ]
        msgs = map(lambda x: ' '.join(map(str,x)),msgs)
        return __MSG_FIELD_SEP.join((__RSP_OK,)+tuple(msgs))

    #STEP TWO++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    elif message.startswith(__REQ_sendfile+__MSG_FIELD_SEP):
        s=message[2:]

        if os.path.exists(s):
            #exists such file
            print' such file already exists in the directory'
            return __RSP_FILE_EXIST
        else:
            #not exists
            sock.sendall(__RSP_OK)
            rsp=tcp_receive(sock)
            with open(s, 'w') as file_to_save:
                file_to_save.write(rsp)
            file_to_save.close()
            print' file sucesfully uploaded '
            return __RSP_OK




    else:
        LOG.debug('Unknown control message received: %s ' % message)
        return __RSP_UNKNCONTROL
