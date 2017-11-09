import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()
from socket import socket, AF_INET, SOCK_STREAM
from socket import error as soc_error
from sys import exit
import server_protocol
from threading import Thread
from argparse import ArgumentParser
___NAME = 'Sudoku Server'
___VER = '0.1.0.0'
___DESC = 'Sudoku Server (TCP version)'
___BUILT = '2017-07-11'
___VENDOR = 'Copyright (c) 2017 Univeristy of Tartu Students team'
__DEFAULT_SERVER_PORT = 8888
__DEFAULT_ADDRESS = "127.0.0.1"
TCP_RECEIVE_BUFFER_SIZE=1024*1024
def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)

    # Starting server

def send_receive(__server_socket, __client_socket):
    m = ''  # Here we collect the received message
    try:
        m = client_socket.recv(TCP_RECEIVE_BUFFER_SIZE)
    except (soc_error, MBoardProtocolError) as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted receiving the data from %s:%d, ' \
                  'error: %s' % (source + (e,)))
        # ... and close socket
        __disconnect_client(client_socket)
        client_socket = None
        # ... and proceed to next client waiting in to accept
        #continue

    # In case message (m) has less then bare minimal of Mboard
    # protocol PDU ( 1 control char and delimiter ),
    # we definitely do not want to server this kind of client ...
    if len(m) <= 2:
        __disconnect_client(client_socket)
        client_socket = None
        # ... and we should proceed to the others
        #continue

    # Now here we assume the message contains
    LOG.debug('Received message [%d bytes] ' \
              'from %s:%d' % ((len(m),) + source))
    # Issue MBoard protocol to process the
    # request message (m) send from the client (source)
    r = protocol.server_process(board, m, source, client_socket)
    # Try to send the response (r) to client
    # Shutdown the TX pipe of the socket after sending
    try:
        LOG.debug('Processed request for client %s:%d, ' \
                  'sending response' % source)
        # Send all data of the response (r)
        client_socket.sendall(r)
    except soc_error as e:
        # In case we failed in the middle of transfer we should report error
        LOG.error('Interrupted sending the data to %s:%d, ' \
                  'error: %s' % (source + (e,)))
        # ... and close socket
        __disconnect_client(client_socket)
        client_socket = None

        # ... and we should proceed to the others
        #continue
threads=[]
# Serve forever
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^argument parser
parser = ArgumentParser(description=__info(),
                            version = ___VER)
parser.add_argument('-a','--address',\
                        help='Server INET address',\
                        default=__DEFAULT_ADDRESS
                        )
parser.add_argument('-p','--port', type=int,\
                        help='Server UDP port, '\
                        'defaults to %d' % __DEFAULT_SERVER_PORT, \
                        default=__DEFAULT_SERVER_PORT)
args = parser.parse_args()
LOG.info('%s version %s started ...' % (___NAME, ___VER))
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Declaring TCP socket

__server_socket = socket(AF_INET, SOCK_STREAM)
server = (args.address,int(args.port))
LOG.debug('Server socket created, descriptor %d' % __server_socket.fileno())
# Bind TCP Socket
try:
    #__server_socket.bind((args.listenaddr, int(args.listenport)))
    __server_socket.bind(server)
except soc_error as e:
    LOG.error('Can\'t start MBoard server, error : %s' % str(e) )
    exit(1)
LOG.debug('Server socket bound on %s:%d' % __server_socket.getsockname())
# Put TCP socket into listening state
__server_socket.listen(3)
LOG.info('Accepting requests on TCP %s:%d' % __server_socket.getsockname())

while 1:
    try:
        LOG.debug('Awaiting new client connections ...')
        # Accept client's connection store the client socket into
        # client_socket and client address into source
        client_socket,source = __server_socket.accept()

        #make thread , pass the function and arguments client sock and server sock
        t=thread(target=send_receive,args=(__server_socket, __client_socket))
        threads.append(t)



        # At this point the request/response sequence is over, we may
        # close the client socket and proceed to the next client
        __disconnect_client(client_socket)
        client_socket=None


    except KeyboardInterrupt as e:
        LOG.debug('Crtrl+C issued ...')
        LOG.info('Terminating server ...')
        break

# If we were interrupted, make sure client socket is also closed
if client_socket != None:
    __disconnect_client(client_socket)

# Close server socket
__server_socket.close()
LOG.debug('Server socket closed')