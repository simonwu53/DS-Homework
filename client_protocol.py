# Imports----------------------------------------------------------------------

# setup logging----------------------------------------------------------------
import logging
import time

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

# message separator
MSG_SEP = ':'
DATA_SEP = '/'
# Protocol Recv Size ---------------------------------------------------------
MAX_RECV_SIZE = 1024

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

              
def publish(socket, message):
    
    if len(message) < 1:
        #LOG.degug('Not enough data received from %s ' % message)
        return __RSP_BADFORMAT
        
    # Try converting to utf-8
    #msg = message.encode('utf-8')
    
    # Extract messageuest type and message argument
    #r_type = msg[0]
    #args = msg[2:]
    
    # Envelope the messageuest
    #message = MSG_SEP.join([r_type]+map(str,args))
    
    # Try to Send messageuest using TCP
    n = 0   # Number of bytes sent
    try:
        socket.sendall(message)
    except:
        # In case we failed in the middle of transfer we should report error
        #LOG.error('Interrupted sending the data to %s:%d, '\
        #            'error: %s' % (socket+(e,)))
        return __RSP_ERRTRANSM

    # Info about bytes sent
    #LOG.info('Sent [%s] messageuest, total bytes sent [%d]'\
    #         '' % (__CTR_MSGS[r_type], n))
             
    # We assume if we are here we succeeded with sending, and
    # we may start receiving
    rsp = None
    try:
        rsp = socket.recv(1024)
    except:
        # In case we failed in the middle of transfer we should report error
        #LOG.error('Interrupted receiving the data from %s:%d, '\
        #          'error: %s' % (socket+(e,)))
        return __RSP_ERRTRANSM
    
    # Info about bytes received
    #LOG.debug('Received response [%d bytes] in total' % len(rsp))
    
    # Check response
    r_data = rsp.split(MSG_SEP)
    rsp_type,rsp_args = r_data[0],r_data[1] #if len(r_data) > 1 else []
            
    return rsp_type,rsp_args

