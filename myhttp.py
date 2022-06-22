#!/usr/bin/python3
import socket
import sys
import os
import signal
import errno
import subprocess
from urllib.parse import urlparse

phrase = {'200':'OK', '404':'File Not Found',
          '500':'Internal Server Error', '501': 'Not Implemented'}

def shutdownServer(signum, frame):
    print("server shutdown ...")
    sys.exit(0)

def collectZombie(signum, frame): #병행처리를 위해 fork()로 process자식 생성 후 좀비되었을 시 signal로 알림을 받기 위하여
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except:
            break

def getFile(fileName): #파일 존재시 정상작동 없을 시 404에러 출력
    try:
        reqFile = open(fileName, 'r')
        code = '200'
        body = reqFile.read()
    except FileNotFoundError as e:
        code = '404'
        body = '<HTML><HEAD><link rel="short icon" href="#"></HEAD>'\
                       '<BODY><H1>404 File Not Found</H1></BODY></HTML>'
    return (code, body)

def doCGI(cgiProg, qString):#GET방식으로 서버 구축하기 위한 함수
    envCGI = dict(os.environ, QUERY_STRING=qString)
    prog = './' + cgiProg
    print(prog)
    try:
        proc = subprocess.Popen([prog], env=envCGI, stdout=subprocess.PIPE)
        #GET방식은 데이터를 CGI환경변수로 전송 출력은 POST랑 동일

        code = '200'
        body = proc.communicate()[0].decode() #pipe byte stream -> unicode
    except Exception as e:
        code = '500'
        body = '<HTML><HEAD><link rel="short icon" href="#"></HEAD>' \
                       '<BODY><H1>500 Internal Sever Error</H1></BODY></HTML>'
        pass
    return (code, body)

def doPOSTCGI(cgiProg, qString): #POST방식으로 서버 구축하기 위한 함수
    prog = './' + cgiProg
    print(prog)
    try:
        proc = subprocess.Popen([prog], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #POST방식은 데이터를 PIPE를 통해 CGI 표준입력으로 전송 출력은 GET이랑 동일

        code = '200'
        body = proc.communicate(qString.encode())[0].decode() #pipe byte stream -> unicode
    except Exception as e:
        code = '500'
        body = '<HTML><HEAD><link rel="short icon" href="#"></HEAD>' \
               '<BODY><H1>500 Internal Sever Error</H1></BODY></HTML>'
        pass
    return (code, body)

def doHTTPService(sock) :
    try :
        reqMessage = sock.recv(RECV_BUFF)
    except ConnectionResetError as e :
        sock.close()
        return

    if reqMessage :
        msgString = bytes.decode(reqMessage)
        print(msgString)
        lines = msgString.split('\r\n')
        reqLine = lines[0]
        fields = reqLine.split(' ')
        method = fields[0]
        reqURL = fields[1]

        postquery = lines[-1]

    else :  # client closed the connection
        sock.close()
        return

    if method == 'GET':
        #login_GET_form.html 실행 GET방식으로 받을 시 login_GET.cgi실행

        r = urlparse(reqURL)
        if r.path == '/':
            fileName = 'index.html'
        else :
            fileName = r.path[1:]

        try:
            fileType = fileName.split('.')[1]
            if fileType.lower() == 'cgi': # process CGI
                code, responseBody = doCGI(fileName, r.query)
            else :   # read the requested file
                code, responseBody = getFile(fileName)
        except Exception as e:
            code, responseBody = getFile(fileName)

    elif method == 'POST':
        #login_POST_form.html 실행 GET방식으로 받을 시 login_POST.cgi실행

        r = urlparse(reqURL)
        if r.path == '/':
            fileName = 'index.html'
        else :
            fileName = r.path[1:]

        try:
            fileType = fileName.split('.')[1]
            if fileType.lower() == 'cgi': # process CGI
                code, responseBody = doPOSTCGI(fileName, postquery)
            else :   # read the requested file
                code, responseBody = getFile(fileName)
        except Exception as e:
            code, responseBody = getFile(fileName)
    else:
        code = '501'
        responseBody = '<HTML><HEAD><link rel="short icon" href="#"></HEAD>' \
                       '<BODY><H1>501 Method Not Implemented</H1></BODY></HTML>'

    statusLine = f'HTTP/1.1 {code} {phrase[code]}\r\n'
    headerLine1 = 'Server: vshttpd 0.1\r\n'
    headerLine2 = 'Connection: close\r\n'
    headerLine3 = f'Contents Length: {len(responseBody)}bytes\r\n\r\n'
    #print(len(responseBody))
    sock.sendall(statusLine.encode())
    sock.sendall(headerLine1.encode())
    sock.sendall(headerLine2.encode())
    sock.sendall(headerLine3.encode())
    sock.sendall(responseBody.encode())

    sock.close()

HOST_IP = '203.250.133.88'
PORT = 10111
BACKLOG = 5
RECV_BUFF = 10000

signal.signal(signal.SIGINT, shutdownServer)
signal.signal(signal.SIGCHLD, collectZombie)

try :
    connSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except :
    print("failed to create a socket")
    sys.exit(1)

try:  # user provided port may be unavaivable
    connSock.bind((HOST_IP, PORT))
except Exception as e:
    print("failed to acquire sockets for port {}".format(PORT))
    sys.exit(1)

print("server running on port {}".format(PORT))
print("press Ctrl+C (or $kill -2 pid) to shutdown the server")

connSock.listen(BACKLOG)

while True:
    print("waiting a new connection...")
    try :
        dataSock, addr = connSock.accept()
        print("got a connection request from: {}".format(addr))
    except IOError as e :
        code, msg = e.args
        if code == errno.EINTR :
            continue
        else :
            raise

    pid = os.fork()
    if pid == 0 :
        doHTTPService(dataSock)
        sys.exit(0)

    dataSock.close()
