import SocketServer
import sys
import logging
import socket
import struct
import select

def send_all(sock, data):
    byte_sent = 0
    while True:
        r = sock.send(data[byte_sent:])
        if r < 0:
            return r
        byte_sent += r
        if byte_sent == len(data):
            return byte_sent

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True

class Sock5Server(SocketServer.StreamRequestHandler):
    def handle_tcp(self, sock, remote):
        try:
            fdset = [sock, remote]
            while True:
                r, w, e = select.select(fdset, [], [])
                if sock in r:
                    data = sock.recv(4096)
                    if len(data) <= 0:
                        break
                    result = send_all(remote, data)
                    if result < len(data):
                        raise Exception('failed to send all data')

                if remote in r:
                    data = remote.recv(4096)
                    if len(data) <= 0:
                        break
                    result = send_all(sock, data)
                    if result < len(data):
                        raise Exception('failed to send all data')
        finally:
            sock.close()
            remote.close()

    def handle(self):
        try:
            sock = self.connection
            sock.recv(100)
            sock.send("\x05\x00")
            data = self.rfile.read(4) or '\x00' * 4
            mode = ord(data[1])
            if mode != 1:
                logging.warn('mode != 1')
                return
            addrtype = ord(data[3])
            if addrtype == 1:
                addr_ip = self.rfile.read(4)
                addr = socket.inet_ntoa(addr_ip)
            elif addrtype == 3:
                addr_len = self.rfile.read(1)
                addr = self.rfile.read(ord(addr_len))
            elif addrtype == 4:
                addr_ip = self.rfile.read(16)
                addr = socket.inet_ntop(socket.AF_INET6, addr_ip)
            else:
                logging.warn('addr_type not support')
                return
            addr_port = self.rfile.read(2)
            port = struct.unpack('>H', addr_port)
            try:
                reply = "\x05\x00\x00\x01"
                reply += socket.inet_aton('0.0.0.0') + struct.pack(">H", 2222)
                self.wfile.write(reply)
                # reply immediately
                remote = socket.create_connection((addr, port[0]))
                logging.info('connecting %s:%s' % (addr, str(port)))
            except socket.error, e:
                logging.warn(e)
                return
            self.handle_tcp(sock, remote)
        except socket.error, e:
            logging.warn(e)


def main():
    global PORT, LOCAL, IPv6
    KEY = None
    LOCAL = "127.0.0.1"
    PORT = 8008
    IPv6 = False

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')

    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])

    try:
        if IPv6:
            ThreadingTCPServer.address_family = socket.AF_INET6
        server = ThreadingTCPServer((LOCAL, PORT), Sock5Server)
        server.serve_forever(poll_interval=0.5)
        logging.info("Server start on %s" % (server.server_address[:]))
        server.serve_forever()
    except socket.error as e:
        logging.error(e)
    except KeyboardInterrupt:
        server.shutdown()
        logging.info("server is shut down")
        sys.exit(0)

if __name__ == "__main__":
    main()







