import SocketServer
import sys
import logging
import socket
import struct
import select
import urlparse

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

class HttpProxyServer(SocketServer.StreamRequestHandler):
    headers = {}
    request = ""
    header = ""
    dest = None

    def handle_it(self, sock, remote):
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
            header = sock.recv(4086)
            index = header.find("\r")
            if index < 0:
                return
            first_line = header[:index]
            self.request = header
            self.headers["method"], self.headers["path"], self.headers["protocol"] = first_line.split()
            url = urlparse.urlparse(self.headers['path'])
            hostname = url.netloc
            port = "80"
            if hostname.find(':') > 0:
                addr, port = hostname.split(':')
            else:
                addr = hostname
            port = int(port)
            # ip = socket.gethostbyname(addr)
            remote = socket.create_connection((addr, port))
            remote.send(self.request)
            self.handle_it(sock, remote)

        except socket.error as e:
            logging.warn(e)

def main():
    global LOCAL, PORT
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
        server = ThreadingTCPServer((LOCAL, PORT), HttpProxyServer)
        logging.info("Server start on %s" % (LOCAL))
        server.serve_forever(poll_interval=0.5)
    except socket.error as e:
        logging.error(e)
    except KeyboardInterrupt:
        server.shutdown()
        logging.info("server is shut down")
        sys.exit(0)

if __name__ == "__main__":
    main()