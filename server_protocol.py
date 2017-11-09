import logging
import time
import numpy as np
import sudoku_generator
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
# client requests
__REQ_REG = '1'
__REQ_JOIN = '2'
__REQ_MOVE = '3'
__REQ_QUIT = '4'
# server requests(notify)
__REQ_STARTGAME = '5'
__REQ_WINNER = '6'
__REQ_NOTIFY = '7'
__CTR_MSGS = {__REQ_REG: 'Register user name in server', # client recv OK or ___
              __REQ_MOVE: 'Player suggest one attempt', # client recv OK or ___
              __REQ_JOIN: 'Request to join game session', # client recv OK or ___
              __REQ_QUIT: 'Player leave game session', # client recv can be none
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
__RSP_LATEMOVE = '6'
__ERR_MSGS = {__RSP_OK: 'No Error',
              __RSP_BADFORMAT: 'Unknown message',
              __RSP_UNKNCONTROL: 'Unknown header',
              __RSP_DUPNAME: 'Duplicated name',
              __RSP_JOINFAIL: 'Fail to join game session',
              __RSP_WRONGMOVE: 'Player suggest wrong answer, -1 score',
              __RSP_LATEMOVE: 'Player''s move was late'
              }
def server_process(message):
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
        split_msg=msg.split(',')
        var=split_msg[0]
        if var.isdigit():
             #if user wants to join existing game
            game_id=int(var)
            if(len(user)>game[game_id][1]):
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
            return __MSG_SEP.join((__RSP_OK,)+str_id)
    if message.startswith(REQ_SUDOKU + MSG_SEP):
        for key in game:





    #if message.startswith(__REQ_USER + MSG_SEP):
    #if message.startswith(__REQ_MOVE + MSG_SEP):
    #    msg=message[2:]







        LOG.debug('Registering new user ')
        LOG.info('Published new message, uuid: %d' % m_id)
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
