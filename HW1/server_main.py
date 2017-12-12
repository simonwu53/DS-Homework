import logging
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.DEBUG,format=FORMAT)

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

# define function for disconnecting client... takes client_socket as an argument
def __disconnect_client(s):
    try:
        s.fileno()
    except soc_error:
        logging.debug('Socket closed already.')
        return

    s.close()
    logging.debug('disconnected client.')

# for each client thread function sends adn receives messages from the client
#function send_receive takes server's socket and client's socket as arguments
def send_receive(__server_socket, client_socket):
    while True:
        m = ''  # Here we collect the received message
        try:
            m = client_socket.recv(TCP_RECEIVE_BUFFER_SIZE)# Here we take message from client
        except (soc_error) as e:
            # In case we failed in the middle of transfer we should report error
            logging.error('Interrupted receiving the data from %s:%d, ' \
                      'error: %s' % (client_socket, e))
            # close socket
            __disconnect_client(client_socket)
            client_socket = None
            #proceed to next client waiting in to accept

        # Now here we assume the message contains
        logging.debug('Received message from %s' % (client_socket))

    #call the server process function from server protocol send message and client_Socket
    #as arguments get three values, one response and two notification threads
        r, notify, sudoku = server_protocol.server_process(m, client_socket)
        # if response contains word "close" it means client wants to quit...
        # send OK and close socket
        if r == 'close':
            client_socket.sendall(server_protocol.__RSP_OK)
            __disconnect_client(client_socket)
            break
        else:
            try:
                logging.debug('Processed request for client %s, ' \
                          'sending response' % client_socket)
                # Send all data of the response (r)
                client_socket.sendall(r)
            except soc_error as e:
                # In case we failed in the middle of transfer
                logging.error('Interrupted sending the data, ' \
                          'error: %s' %  (e,))
                # close socket
                __disconnect_client(client_socket)
        # start notification threads if there is any content
        if notify:
            notify.start()
            logging.debug('notification1 create')
        if sudoku:
            sudoku.start()
            logging.debug('notification2 create')

        # proceed to the others

"""main function"""
if __name__ == '__main__':
    threads=[] # collecting the threads for each client in a list
    # Declaring TCP socket
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
    logging.info('%s version %s started ...' % (___NAME, ___VER))

    __server_socket = socket(AF_INET, SOCK_STREAM)
    server = (args.address,int(args.port))
    logging.debug('Server socket created, descriptor %d' % __server_socket.fileno())
    # Bind TCP Socket
    try:
        __server_socket.bind(server)
        logging.debug('Server socket bound on %s:%d' % __server_socket.getsockname())
    except soc_error as e:
        logging.error('Can\'t start server, error : %s' % str(e) )
        exit(1)

    # Put TCP socket into listening state
    __server_socket.listen(5)
    logging.info('Accepting requests on TCP %s:%d' % __server_socket.getsockname())

    while 1:
        try:
            logging.debug('Awaiting new client connections ...')
            # Accept client's connection store the client socket into
            # client_socket and client address into source
            client_socket,source = __server_socket.accept()
            logging.debug('connected %s' %(client_socket))

            #make thread , pass the function and arguments client sock and server sock
            t=Thread(target=send_receive,args=(__server_socket, client_socket))
            threads.append(t)
            t.start()

        except KeyboardInterrupt as e:
            logging.debug('Crtrl+C issued ...')
            logging.info('Terminating server ...')
            break


