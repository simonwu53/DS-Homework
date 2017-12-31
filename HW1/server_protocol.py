import logging
import sudoku_generator
import operator
from threading import Thread
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)


# dictionaries
game = {} # game sessions information are stored
MSG_SEP = ':'
DATA_SEP= '/'
user_names=[] #here are stored all the usernames
score={} #here username and score will be stored
sudoku = [] #here will be stored sudoku and player limits
user={} #this dictionary contains game_id as key which correspondes to the players with their scores and client's sockey
id=0 # game id , it will be increased as new games are created one by one
#sudoku_generator=[]
answers={}
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
    message = __REQ_WINNER + MSG_SEP + winner_user + DATA_SEP + str(user_dict[winner_user][0]) 
    
    return message
    
    
def notify(gameid):
    user_score_string = ''
    #get user:score data
    user_score_dict = user[gameid]
    print user_score_dict
    #assemble the message
    for i in user_score_dict.items():
        user_score_string += i[0] + DATA_SEP + str(i[1][0]) + MSG_SEP
        
    message = __REQ_NOTIFY + MSG_SEP + user_score_string
    print message
    return message
    
    
def sudoku1(gameid):
    
    #get sudoku
    sudoku = game[gameid][0]
    
    #assemble the message
    message = __REQ_SUDOKU + MSG_SEP + ''.join(sudoku)    
    
    return message
    
def notification_thread(message,gameid):

    #find client sockets by id: in user dict
    logging.debug('process notification')
    user_dict =  user[gameid]
    user_list = user_dict.items()

    for i in range (len(user_list)):
        client_socket = user_list[i][1][1]
        client_socket.sendall(message)
    logging.debug('notification sent')
    return
    
def server_process(message, client_socket):
    global sudoku
    global id
    '''Process the client's message,
        @param message: string, protocol data unit received from client
        @returns string, response to send to client
    '''
    logging.debug('Received request [%d bytes] in total' % len(message))
    if len(message) < 2:
        logging.debug('Not enough data received from %s ' % message)
        return __RSP_BADFORMAT,None,None
    logging.debug('Request control code (%s)' % message[0])
    if message.startswith(__REQ_REG + MSG_SEP):
        # user wants to register
        msg = message[2:]
        if msg in user_names:
            #name already in use
            return __RSP_DUPNAME,None,None
        else:
            #such name does not exist, user will be registered
            user_names.append(msg)
            return __RSP_OK,None,None
    if message.startswith(
                    __REQ_JOIN + MSG_SEP):  # here is 2 step a) user wants to join existing game or b)creating new game
        msg = message[2:]

        split_msg = msg.split(DATA_SEP)
        var = split_msg[0]

        try:
            game_id = int(var)
            # if user wants to join existing game
            name = split_msg[1]
            game_id = int(var)
            if (len(user[game_id]) > game[game_id][1]):
                return __RSP_JOINFAIL, None, None  # limit is already reached at this game session
            user[game_id][name] = [0,
                                   client_socket]  # otherwise user is registered to the wanted game session and started from the score 0.
            print user[game_id]
            if (len(user[game_id]) == game[game_id][1]):  # if limit is full
                message = startgame()
                t = Thread(target=notification_thread, args=(message, game_id))
                return __RSP_OK, t, None
            else:  # notify player joined
                message = notify(game_id)
                t = Thread(target=notification_thread, args=(message, game_id))
                return __RSP_OK, t, None
        except ValueError:
            sudoku = []
            name = split_msg[0]
            limit = split_msg[1]  # error1
            difficulty = split_msg[2]
            id += 1  # game ids will start from 1
            str_id = str(id)
            sudoku_answer, generated_sudoku = sudoku_generator.setup_sudoku(difficulty)
            print sudoku_answer
            sudoku.append(generated_sudoku)
            sudoku.append(limit)
            game[id] = sudoku
            answers[id] = sudoku_answer
            score[name] = [0, client_socket]  # saving score and client socket
            user[id] = score
            return __RSP_OK + MSG_SEP + str_id, None, None
        #if var.isdigit():

        #else:  # else user wants to create new session


    if message.startswith(__REQ_SUDOKU + MSG_SEP):
        #fetching all the sudokus and game ids
        msg = ''
        for key in game:
            numb_players = str(len(user[key]))
            msg += str(key) + DATA_SEP + ''.join(game[key][0]) + DATA_SEP + game[key][1] + DATA_SEP + numb_players
        msg += MSG_SEP
        return __RSP_OK + MSG_SEP + msg,None,None
        # 1:1/1234/5/4:   this kind of string will be returned. header:gameid:sudoku:limit:players
    if message.startswith(__REQ_USER + MSG_SEP):
        msg1 = message[2:]
        split_msg = msg1.split(DATA_SEP)
        game_id = split_msg[0]
        msg = ''

        game_id = int(game_id)
        for user_name in user[game_id]:  # will be returned in request_user
            msg +=  user_name + DATA_SEP + str(user[game_id][user_name][0]) + MSG_SEP

        return __RSP_OK + MSG_SEP + msg,None,None
        # 1:user4/0:User2/5:user3/8:user1/0:  this kind of string will be returned . header:username/score:username/score:

    if message.startswith(__REQ_QUIT + MSG_SEP): # user wants to quit. So his score will be deleted.
        msg = message[2:]
        split_msg = msg.split(DATA_SEP)
        user_name = split_msg[1]
        game_id = split_msg[0]
        if split_msg[2] == 'close':   # if client wants to close the socket , request for closing his socket
            #will be sent to the server.
            return 'close', None, None
        else: #only delete the user don't close the socket
            game_id = int(game_id)
            del user[game_id][user_name]

            if len(user[game_id]) == 0: #if no user left to the game session
                del user[game_id]
                del game[game_id]
                del answers[game_id]
                return __RSP_OK, None, None
            else: #notify that someone quitted
                message = notify(game_id)
                t = Thread(target=notification_thread, args=(message, game_id))
                return __RSP_OK,t,None
    if message.startswith(__REQ_MOVE + MSG_SEP):  # user did the step move
        msg = message[2:]
        split_msg = msg.split(DATA_SEP)
        gid = int(split_msg[0])
        sudoku = game[gid][0]
        position = int(split_msg[2])
        number = split_msg[3]
        player = split_msg[1]
        if sudoku[position] =='_': # if position is free

            correct_number = answers[gid][position] #find correct number in the sudoku answers

            if number == correct_number:  #if the number is correct
                x = user[gid][player][0] #find the user's previous score
                x += 1  #increase by one
                str(x) #make it string and update the score
                user[gid][player][0] = x
                logging.debug("correct move")
                sudoku[position] = number #put the new number in the sudoku
                if answers[gid] == game[gid][0]: # check if sudoku is full and notify the winner and users
                    message=winner(gid)
                    t = Thread(target=notification_thread, args=(message, gid))
                    return __RSP_OK,t,None
                else: # Game not finished notify the users about changed scores and sudoku
                    message=notify(gid)
                    t = Thread(target=notification_thread, args=(message, gid))
                    message1=sudoku1(gid)
                    t1=Thread(target=notification_thread, args=(message1, gid))
                    return __RSP_OK, t, t1
            else: #wrong move , decrease the score of the user and update the scores, notify the users about changes
                x = int(user[gid][player][0])
                x -= 1
                str(x)
                user[gid][player][0] = x
                logging.debug("wrong move")
                message = notify(gid)
                t = Thread(target=notification_thread, args=(message, gid))
                return __RSP_WRONGMOVE,t,None
        else: #late move
            logging.debug("late move")
            return __RSP_LATEMOVE,None,None


    else:
        logging.debug('Unknown control message received: %s ' % message)
        return __RSP_UNKNCONTROL,None,None

