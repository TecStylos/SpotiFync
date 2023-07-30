import socket

def connect(host : str, port : int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock

def listen(host : str, port : int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen()
    return sock

def close(sock):
    sock.close()

def sendmsg(sock, msg : str):
    msg = msg.encode(encoding="utf-8")
    msg = len(msg).to_bytes(4, byteorder="big") + msg
    sock.sendall(msg)

def recvmsg(sock):
    msglen = int.from_bytes(sock.recv(4), byteorder="big")
    msg = sock.recv(msglen).decode(encoding="utf-8")
    return msg