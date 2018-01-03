from threading import Thread, Event
from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOL_IP
from socket import IPPROTO_IP, IP_MULTICAST_LOOP, IP_MULTICAST_TTL
from socket import inet_aton, IP_ADD_MEMBERSHIP, socket
from socket import error as soc_err
from time import sleep
import logging as log

"""---------------------------------------------------------------------------------------------------------------------
                                            LOGGING
---------------------------------------------------------------------------------------------------------------------"""
DEFAULT_LOG_LEVEL = log.DEBUG
DEFAULT_LOG_FORMAT = \
    '%(asctime)-15s (%(threadName)-2s) %(levelname)s %(message)s'
log.basicConfig(level=log.DEBUG, format=DEFAULT_LOG_FORMAT)

"""---------------------------------------------------------------------------------------------------------------------
                                            Constant
---------------------------------------------------------------------------------------------------------------------"""
DEFAULT_RCV_BUFFSIZE = 1024
WHOISHERE = '19Kadir'
MSG_FIELD_SEP = '>.<'

"""---------------------------------------------------------------------------------------------------------------------
                                            Detection
    variables: addr, port, buffer_size
---------------------------------------------------------------------------------------------------------------------"""


class detect_server(Thread):
    def __init__(self, mcast_addr, mcast_port, mcast_rcv_buffer_size=DEFAULT_RCV_BUFFSIZE):
        self.server_list = []
        # initial thread
        Thread.__init__(self, name=self.__class__.__name__)
        # set buffer size
        self.__rcv_bsize = mcast_rcv_buffer_size
        # Declare UDP socket
        self.__s = socket(AF_INET, SOCK_DGRAM)
        log.debug('UDP socket declared ...')

        # Reusable UDP socket? I am not sure we really need it ...
        self.__s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        log.debug('UDP socket reuse set ...')

        # Enable loop-back multi-cast - the local machine will also receive multicasts
        self.__s.setsockopt(IPPROTO_IP, IP_MULTICAST_LOOP, 1)
        log.debug('Enabled loop-back multi-casts ...')

        # Bind UDP socket to listen to muli-casts
        self.__s.bind((mcast_addr, mcast_port))
        log.debug('Socket bound to %s:%s' % self.__s.getsockname())

        # Register for multi-cast group, and sets listening all origins
        # (all interfaces 0.0.0.0)
        self.__s.setsockopt(SOL_IP, IP_ADD_MEMBERSHIP, inet_aton(mcast_addr) + inet_aton('0.0.0.0'))
        log.debug('Subscribed for multi-cast group %s:%d' % (mcast_addr, mcast_port))

    def __protocol_rcv(self, msg, src):
        if not msg.startswith(WHOISHERE + MSG_FIELD_SEP):
            log.warn('Unexpected multi-cast [%s]' % msg)
            return

        # Compare peer address from message and actual remote socket address
        try:
            # get server queue
            peer_addr_from_msg = msg.split(MSG_FIELD_SEP)[1]
        except Exception as e:
            log.warn('Can not parse payload [%s], error: %s' \
                     '' % (msg.split(MSG_FIELD_SEP)[1], str(e)))
            return
        # log.debug('Server queue: %s' % peer_addr_from_msg)
        # log.debug('Peer candidate address from socket [%s:%d]' % src)
        return peer_addr_from_msg

    def receiver_loop(self):
        # Listen forever (Ctrl+C) to kill
        try:
            while 1:
                # Receive multi-cast message
                message, addr = self.__s.recvfrom(self.__rcv_bsize)
                # log.debug('Received Multicast From: %s:%s [%s]' % (addr + (message,)))
                server_q = self.__protocol_rcv(message, addr)
                # if server not in the list, append into server list
                if server_q not in self.server_list:
                    self.server_list.append(server_q)
                    # print self.server_list
        except soc_err as e:
            log.warn('Socket error: %s' % str(e))
        except (KeyboardInterrupt, SystemExit):
            log.info('Ctrl+C issued, terminating ...')
        finally:
            self.__s.close()
        log.debug('Terminating ...')

    def run(self):
        self.receiver_loop()

    def stop(self):
        self.__s.close()

    def getlist(self):
        return self.server_list


"""---------------------------------------------------------------------------------------------------------------------
                                            Main
    This is an example usage. Implement it in server main.
---------------------------------------------------------------------------------------------------------------------"""
if __name__ == '__main__':
    log.info('Application start ...')
    # multicast addr, port
    mc_ip, mc_port = '239.1.1.1', 7778
    # run server detection
    mc = detect_server(mc_ip, mc_port)
    mc.daemon = True
    mc.start()

    # stop receiving multicasting
    # can't stop
    # run forever
    # mc.join()

    sleep(60)
    mc.stop()
    print 'exit'

