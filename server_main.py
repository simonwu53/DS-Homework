import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)
LOG = logging.getLogger()
from socket import socket, AF_INET, SOCK_STREAM
from socket import error as soc_error
from sys import exit
import server_protocol
from threading import Thread
___NAME = 'Sudoku Server'
___VER = '0.1.0.0'
___DESC = 'Sudoku Server (TCP version)'
___BUILT = '2017-07-11'
___VENDOR = 'Copyright (c) 2017 Univeristy of Tartu Students team'
TCP_RECEIVE_BUFFER_SIZE=1024*1024
def __info():
    return '%s version %s (%s) %s' % (___NAME, ___VER, ___BUILT, ___VENDOR)
# Not a real main method-------------------------------------------------------
    '''Runs the Mboard server
    should be run by the main mehtod of CLI or GUI application
    @param args: ArgParse collected arguments
    '''
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

        # Now here we assumen the message contains
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
LOG.info('%s version %s started ...' % (___NAME, ___VER))


# Declaring TCP socket
__server_socket = socket(AF_INET,SOCK_STREAM)
LOG.debug('Server socket created, descriptor %d' % __server_socket.fileno())
# Bind TCP Socket
try:
    __server_socket.bind((args.listenaddr,int(args.listenport)))
except soc_error as e:
    LOG.error('Can\'t start MBoard server, error : %s' % str(e) )
    exit(1)
LOG.debug('Server socket bound on %s:%d' % __server_socket.getsockname())
# Put TCP socket into listening state
__server_socket.listen(__DEFAULT_SERVER_TCP_CLIENTS_QUEUE)
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

        # in function receive msg, send to server protocol,receive resp, send it to client
        LOG.debug('New client connected from %s:%d' % source)

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