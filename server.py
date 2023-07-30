import connection as cnn
import threading

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 42069

lock = threading.Lock()
HOST_SOCK = []
CLIENT_SOCKS = []

def runHostThread():
    with lock:
        host = HOST_SOCK[0]

    while True:
        try:
            msg = cnn.recvmsg(host)
        except:
            print("Host disconnected")
            break

        print("Broadcasting message... ")
        with lock:
            for client in CLIENT_SOCKS:
                try:
                    cnn.sendmsg(client, msg)
                except:
                    print("Client disconnected")
                    cnn.close(client)
                    CLIENT_SOCKS.remove(client)

    with lock:
        HOST_SOCK.pop()

def runClientThread(sock : cnn.socket):
    while True:
        try:
            msg = cnn.recvmsg(sock)
        except:
            print("Client disconnected")
            break

        print("Sending message to host... ")
        with lock:
            try:
                cnn.sendmsg(HOST_SOCK[0], msg)
            except:
                print("Host disconnected")
                cnn.close(HOST_SOCK[0])
                HOST_SOCK.pop()
                cnn.close(sock)
                break

if __name__ == "__main__":
    while True:
        try:
            print("Starting server...")

            sock = cnn.listen(SERVER_HOST, SERVER_PORT)

            while True:
                print("Waiting for connection...")

                conn, _ = sock.accept()

                print("Waiting for connection mode...")
                mode = cnn.recvmsg(conn)
                if mode == "host":
                    with lock:
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
                    with lock:
                        print("Client connected")
                        CLIENT_SOCKS.append(conn)
                        cnn.sendmsg(conn, "ready")
                        threading.Thread(target=runClientThread, args=(conn,)).start()
                else:
                    print("Invalid mode")
                    cnn.close(conn)
                    continue
        except:
            print("Server crashed")
            print("Restarting...")
            cnn.close(sock)
            
            HOST_SOCK.clear()
            CLIENT_SOCKS.clear()