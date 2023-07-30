import connection as cnn

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 42069

if __name__ == "__main__":
    sock = cnn.listen(SERVER_HOST, SERVER_PORT)

    while True:
        conn, _ = sock.accept()
        mode = cnn.recvmsg(conn)
        if mode == "host":
            print("Host connected")
        elif mode == "client":
            print("Client connected")
        else:
            print("Invalid mode")
            cnn.close(conn)
            continue
        
        cnn.sendmsg(conn, "ready")