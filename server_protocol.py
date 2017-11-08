import logging
import time

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

# Protocol Recv Size ---------------------------------------------------------
TCP_RECEIVE_BUFFER_SIZE=1024*1024
MAX_PDU_SIZE = 200*1024*1024

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
# Common methods --------------------------------------------------------------
def tcp_send(sock,data):
    '''Send data using TCP socket. When the data is sent, close the TX pipe
    @param sock: TCP socket, used to send/receive
    @param data: The data to be sent
    @returns integer,  n bytes sent and error if any
    @throws socket.errror in case of transmission error
    '''
    sock.sendall(data)
    sock.shutdown(SHUT_WR)
    return len(data)

# Field separator for sending multiple values ---------------------------------
__MSG_FIELD_SEP = ':'
# Exceptions ------------------------------------------------------------------
class MBoardProtocolError(Exception):
    '''Should be thrown internally on client or server while receiving the
    data, in case remote end-point attempts to not follow the MBoard protocol
    '''
    def __init__(self,msg):
        Exception.__init__(self,msg)
# Common methods --------------------------------------------------------------
def tcp_send(sock,data):
    '''Send data using TCP socket. When the data is sent, close the TX pipe
    @param sock: TCP socket, used to send/receive
    @param data: The data to be sent
    @returns integer,  n bytes sent and error if any
    @throws socket.errror in case of transmission error
    '''
    sock.sendall(data)
    sock.shutdown(SHUT_WR)
    return len(data)

def tcp_receive(sock,buffer_size=TCP_RECEIVE_BUFFER_SIZE):
    '''Receive the data using TCP receive buffer.
    TCP splits the big data into blocks automatically and ensures,
    that the blocks are delivered in the same order they were sent.
    Appending the received blocks into big message is usually done manually.
    In this method the receiver also expects that the sender will close
    the RX pipe after sending, denoting the end of sending
    @param buffer_size: integer, the size of the block to receive in one
            iteration of the receive loop
    @returns string, data received
    @throws socket.errror in case of transmission error,
            MBoard PDU size exceeded in case of client attempting to
            send more data the MBoard protocol allows to send in one PDU
            (MBoard request or response) - MAX_PDU_SIZE
    '''
    m = ''      # Here we collect the received message
    # Receive loop
    while 1:
        # Receive one block of data according to receive buffer size
        block = sock.recv(TCP_RECEIVE_BUFFER_SIZE)
        # If the remote end-point did issue shutdown on the socket
        # using  SHUT_WR flag, the local end point will receive and
        # empty string in all attempts of recv method. Therefore we
        # say we stop receiving once the first empty block was received
        if len(block) <= 0:
            break
        # There is no actual limit how big the message (m) can grow
        # during the block delivery progress. Still we have to take
        # into account amount of RAM on server when dealing with big
        # messages, and one point introduce a reasonable limit of
        # MBoard PDU (MBoard request/responses).
        if ( len(m) + len(block) ) >= MAX_PDU_SIZE:
            # Close the RX pipe to prevent the remote end-point of sending
            # more data
            sock.shutdown(SHUT_RD)
            # Garbage collect the unfinished message (m) and throw exception
            del m
            raise \
                MBoardProtocolError( \
                    'Remote end-point tried to exceed the MAX_PDU_SIZE'\
                    'of MBoard protocol'\
                )

        # Appending the blocks, assembling the message
        m += block
    return m
