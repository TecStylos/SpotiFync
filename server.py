import connection as cnn
import threading

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 42069

HOST_SOCK = []
CLIENT_SOCKS = []

def runHostThread():
    sock = HOST_SOCK[0]
    while True:
        try:
            print("Waiting for message... ")
            msg = cnn.recvmsg(sock)
        except:
            print("Host disconnected")
            break

        print("Broadcasting message... ")
        for sock in CLIENT_SOCKS:
            try:
                cnn.sendmsg(sock, msg)
            except:
                print("Client disconnected")
                cnn.close(sock)
                CLIENT_SOCKS.remove(sock)

    HOST_SOCK.pop()

if __name__ == "__main__":
    print("Starting server...")

    sock = cnn.listen(SERVER_HOST, SERVER_PORT)

    while True:
        print("Waiting for connection...")

        conn, _ = sock.accept()
        
        print("Waiting for connection mode...")
        mode = cnn.recvmsg(conn)
        if mode == "host":
            if len(HOST_SOCK) > 0:
                print("Duplicate host connected...")
                cnn.sendmsg(conn, "nohostavail")
                cnn.close(conn)
                continue
            print("Host connected")
            HOST_SOCK.append(conn)
            cnn.sendmsg(conn, "ready")
            threading.Thread(target=runHostThread).start()
        elif mode == "client":
            print("Client connected")
            CLIENT_SOCKS.append(conn)
            cnn.sendmsg(conn, "ready")
        else:
            print("Invalid mode")
            cnn.close(conn)
            continue