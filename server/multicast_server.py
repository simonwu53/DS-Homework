from threading import Thread
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
DEFAULT_LOG_FORMAT =\
                '%(asctime)-15s (%(threadName)-2s) %(levelname)s %(message)s'
log.basicConfig(level=log.DEBUG,format=DEFAULT_LOG_FORMAT)


"""---------------------------------------------------------------------------------------------------------------------
                                            Constant
---------------------------------------------------------------------------------------------------------------------"""
DEFAULT_RCV_BUFFSIZE = 1024
WHOISHERE = '19Kadir'
MSG_FIELD_SEP = '>.<'


"""---------------------------------------------------------------------------------------------------------------------
                                          Multicasting
---------------------------------------------------------------------------------------------------------------------"""
def send_whoishere(server_q,mc_addr,ttl=1):
    # Prepare the information about actual server queue
    REQ = WHOISHERE+MSG_FIELD_SEP+ str(server_q)
    try:
        # Here we use temporal socket
        # as it is for multicast sending it will be not bound anyway
        s = socket(AF_INET,SOCK_DGRAM)
        log.debug('UDP socket declared ...')
        # Enable loop-back multi-cast
        s.setsockopt(IPPROTO_IP,IP_MULTICAST_LOOP,1)
        log.debug('Enabled loop-back multi-casts ...')

        if s.getsockopt(IPPROTO_IP, IP_MULTICAST_TTL) != ttl:
            s.setsockopt(IPPROTO_IP,IP_MULTICAST_TTL,ttl)
            log.debug('Set multicast TTL to %d' % ttl)
        s.sendto(REQ,mc_addr)
        log.debug('Multicast sent to [%s:%d]: %s' % (mc_addr+(REQ,)))
        sock_addr = s.getsockname()
        s.close()
        log.debug('Closed multicast sending socket %s:%d' % sock_addr)
    except Exception as e:
        log.warn('Can not send MC request: %s' % str(e))


"""---------------------------------------------------------------------------------------------------------------------
                                             Main
---------------------------------------------------------------------------------------------------------------------"""
if __name__ == '__main__':
    log.info('Application start ...')
    # multicast addr, port
    mc_ip, mc_port = '239.1.1.1', 7778
    # set server queue name
    server_q = 1

    # Emit multicasts
    for _ in range(10):
        send_whoishere(server_q,(mc_ip,mc_port))
        server_q += 1
        sleep(3)

    log.info('Terminating ...')