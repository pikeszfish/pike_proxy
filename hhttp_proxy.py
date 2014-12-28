import socket
import threading
import urlparse
import select

BUF_LEN = 8192
BUFLEN=8192


class MyProxy1(threading.Thread):
    def __init__(self,conn,addr):
        threading.Thread.__init__(self)
        self.source = conn
        self.request = ""
        self.headers = {}
        self.destnation = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    def get_headers(self):
        header = ''
        while True:
            header += self.source.recv(BUFLEN)
            # print (header)
            index = header.find('\n')
            if index > 0:
                break
        #firstLine,self.request=header.split('\r\n',1)
        firstLine = header[:index]
        self.request = header[index+1:]
        self.headers['method'], self.headers['path'], self.headers['protocol'] = firstLine.split()

    def conn_destnation(self):
        url = urlparse.urlparse(self.headers['path'])
        hostname = url.netloc
        port = "80"
        if hostname.find(':') > 0:
            addr,port = hostname.split(':')
        else:
            addr = hostname
        port = int(port)
        print (addr)
        ip = socket.gethostbyname(addr)
        # print ip,port
        self.destnation.connect((ip,port))
        data = "%s %s %s\r\n" %(self.headers['method'],self.headers['path'],self.headers['protocol'])
        # print (data+self.request)
        self.destnation.send(data+self.request)
        print ("send \n" + data + self.request)


    def renderto(self):
        readsocket = [self.destnation]
        while True:
            data = ''
            (rlist,wlist,elist)=select.select(readsocket,[],[],3)
            if rlist:
                data = rlist[0].recv(BUFLEN)
                if len(data) > 0:
                    # print (data)
                    self.source.send(data)
                else:
                    break
    def run(self):
        self.get_headers()
        self.conn_destnation()
        self.renderto()



class MyProxy(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.source = conn
        self.headers = {}
        self.request = ""
        self.destnation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # socket.setdefaulttimeout()

    def get_header(self):
        header = ''
        while True:
            header += self.source.recv(BUF_LEN)
            index = header.find('\r')
            if index > 0:
                break
        first_line = header[:index]
        self.request = header[index+1:]
        self.headers['method'], self.headers['path'], self.headers['protocol'] = first_line.split()

    def conn_destnation(self):
        try:
            result = urlparse.urlparse(self.headers['path'])
        except KeyError as e:
            self.destnation.close()
            return
        port = "80"
        hostname = result.netloc
        if hostname.find(':') > 0:
            addr, port = hostname.split(':')
        else:
            addr = hostname
        port = int(port)
        dest_ip = socket.gethostbyname(addr)
        print (type(dest_ip))
        print (type(port))
        self.destnation.connect((dest_ip, port))
        data = "%s %s %s%s" % (self.headers['method'],   \
                                   self.headers['path'],     \
                                   self.headers['protocol'], \
                                   self.request)
        self.destnation.send(data)
        print ("send \n" + data)
        # print ("send     " + data)

    def render_to(self):
        readsocket=[self.destnation]
        while True:
            data=''
            (rlist, wlist, elist) = select.select(readsocket,[],[],3)
            if rlist:
                data = rlist[0].recv(BUF_LEN)
                if len(data)>0:
                    print ("recv \n" + data)
                    self.source.send(data)
                else:
                    break

    def run(self):
        self.get_header()
        self.conn_destnation()
        self.render_to()

class MyServer(object):
    rec = []
    def __init__(self, host, port, handler=MyProxy):
        self.host = host
        self.port = port
        self.handler = handler
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host,port))
        self.server.listen(5)

    def start(self):
        while True:
            try:
                conn, addr = self.server.accept()
                t = MyProxy1(conn, addr)
                self.rec.append(t)
                t.start()
            except KeyboardInterrupt:
                print ("shit happens")
                for t in self.rec:
                    t.destnation.close()
                exit(0)

if "__main__" == __name__:
    host = '127.0.0.1'
    port = 8008
    MyServer(host, port, MyProxy1).start()






