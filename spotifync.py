import time
import connection as cnn
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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

def getCurrentTimestamp():
    return time.time_ns() // 1000000

def runHost(spotify : spotipy.Spotify, sock : cnn.socket):
    cnn.sendmsg(sock, "host")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return
    
    while True:
        current_playing = spotify.current_playback()
        if current_playing is None:
            print("Nothing is playing")
        else:
            URIs = [ current_playing["item"]["uri"] ]
            positionMs = current_playing["progress_ms"]
            timestamp = current_playing["timestamp"]

            cnn.sendmsg(sock, "playback_info")
            cnn.sendmsg(sock, current_playing["item"]["uri"])
            cnn.sendmsg(sock, str(current_playing["progress_ms"]))
            cnn.sendmsg(sock, current_playing["timestamp"])

        time.sleep(1)

def runClient(spotify, sock):
    cnn.sendmsg(sock, "client")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return

    while True:
        cmd = cnn.recvmsg(sock)
        if cmd == "playback_info":
            hostURI = cnn.recvmsg(sock)
            hostPositionMs = int(cnn.recvmsg(sock))
            hostTimestamp = int(cnn.recvmsg(sock))
            
            current_playback = spotify.current_playback()
            if current_playback is not None:
                myURI = current_playback["item"]["uri"]
                myPositionMs = current_playback["progress_ms"]
                myTimestamp = current_playback["timestamp"]
                predictedPositionMs = hostPositionMs + (myTimestamp - hostTimestamp)
                if myURI == hostURI and abs(myPositionMs - predictedPositionMs) < 1000:
                    continue

            spotify.start_playback(uris=[hostURI], position_ms=hostPositionMs + (getCurrentTimestamp() - hostTimestamp))

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
        mode = input("Enter mode (host/client): ").lower()
        if mode not in ("host", "client"):
            mode = ""
            print("Invalid mode, try again.")

    if mode == "host":
        runHost(spotify, sock)
    elif mode == "client":
        runClient(spotify, sock)