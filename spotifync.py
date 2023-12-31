import time
import connection as cnn
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import queue
import threading

SERVER_HOST = "tecstylos.ddns.net"
SERVER_PORT = 42069

SCOPES = (
	"user-modify-playback-state",
	"user-read-playback-state",
	"user-read-currently-playing",
	"user-read-recently-played",
	"user-top-read",
	"playlist-read-collaborative",
	"playlist-read-private",
	"user-library-read"
)

lock = threading.Lock()
queue = queue.Queue()

def runHostCommandReceiver(sock : cnn.socket):
    while True:
        cmd = cnn.recvmsg(sock)
        with lock:
            queue.put(cmd)

def runHost(spotify : spotipy.Spotify, sock : cnn.socket):
    print("Running in host mode...")

    cnn.sendmsg(sock, "host")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return
    
    threading.Thread(target=runHostCommandReceiver, args=(sock,)).start()
    
    currentProgressMs = 0

    while True:
        current_playing = spotify.current_playback()
        cnn.sendmsg(sock, "playback_info")
        if current_playing is None or not current_playing["is_playing"]:
            cnn.sendmsg(sock, "is_paused")
        else:
            currentProgressMs = current_playing["progress_ms"]

            cnn.sendmsg(sock, "is_playing")
            cnn.sendmsg(sock, current_playing["item"]["uri"])
            cnn.sendmsg(sock, str(current_playing["progress_ms"]))
            cnn.sendmsg(sock, str(current_playing["timestamp"]))

        with lock:
            if not queue.empty():
                cmd = queue.get()
                print("Received command '" + cmd + "'")
            else:
                cmd = None

        if cmd == "play":
            spotify.start_playback()
        elif cmd == "pause":
            spotify.pause_playback()
        elif cmd == "forward":
            spotify.next_track()
        elif cmd == "rewind":
            if currentProgressMs < 10000:
                spotify.previous_track()
            else:
                spotify.seek_track(0)
        elif cmd is not None and cmd.startswith("add "):
            uri = cmd[4:]
            spotify.add_to_queue(uri)
        elif cmd is not None:
            print("Invalid command")

        time.sleep(1)

def runClientCommandSender(sock : cnn.socket):
    while True:
        cmd = input("> ")
        if cmd == "help":
            print("Commands:")
            print("  play")
            print("  pause")
            print("  forward")
            print("  rewind")
            print("  add <spotify uri>")
            print("  help")
            print("  exit")
        elif cmd == "exit":
            cnn.close(sock)
            break
        else:
            cnn.sendmsg(sock, cmd)

def runClient(spotify, sock):
    print("Running in client mode...")

    cnn.sendmsg(sock, "client")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return
    
    threading.Thread(target=runClientCommandSender, args=(sock,)).start()

    while True:
        cmd = cnn.recvmsg(sock)

        if cmd == "playback_info":
            play_state = cnn.recvmsg(sock)
            
            current_playback = spotify.current_playback()

            if play_state == "is_paused":

                if current_playback is not None and current_playback["is_playing"]:
                    spotify.pause_playback()

            elif play_state == "is_playing":

                hostURI = cnn.recvmsg(sock)
                hostPositionMs = int(cnn.recvmsg(sock))
                hostTimestamp = int(cnn.recvmsg(sock))

                if current_playback is not None:
                    myURI = current_playback["item"]["uri"]
                    myPositionMs = current_playback["progress_ms"]
                    myTimestamp = current_playback["timestamp"]
                    predictedPositionMs = hostPositionMs + (myTimestamp - hostTimestamp)

                    if not current_playback["is_playing"]:
                        print("Resuming playback...")
                    elif myURI != hostURI:
                        print("Switching tracks...")
                    elif abs(myPositionMs - predictedPositionMs) > 5000:
                        print("Time difference: " + str(myPositionMs - predictedPositionMs) + "ms")
                        print("Seeking...")
                    else:
                        continue

                    spotify.start_playback(uris=[hostURI], position_ms=predictedPositionMs)
        else:
            print("Invalid command")

if __name__ == "__main__":
    with open("clientID.txt", "r") as f:
        clientID = f.read().strip()
    with open("clientSecret.txt", "r") as f:
        clientSecret = f.read().strip()
    redirectURI = "http://example.com"

    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=clientID, client_secret=clientSecret, redirect_uri=redirectURI, scope=" ".join(SCOPES)))

    sock = cnn.connect(SERVER_HOST, SERVER_PORT)

    mode = ""
    while mode == "":
        mode = input("Enter mode (host/client/reset): ").lower()
        if mode not in ("host", "client", "reset"):
            mode = ""
            print("Invalid mode, try again.")

    if mode == "host":
        runHost(spotify, sock)
    elif mode == "client":
        runClient(spotify, sock)
    elif mode == "reset":
        cnn.sendmsg(sock, "reset")
        cnn.close(sock)
        print("Reset server.")