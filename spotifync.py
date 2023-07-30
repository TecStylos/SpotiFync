from time import sleep
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



def runHost(spotify, sock):
    cnn.sendmsg(sock, "host")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return
    
    while True:
        current_playing = spotify.current_playback()
        if current_playing is None:
            print("Nothing is playing")
        else:
            print("Currently playing:", current_playing["item"]["name"])

        sleep(1)

def runClient(spotify, sock):
    cnn.sendmsg(sock, "client")
    if cnn.recvmsg(sock) != "ready":
        print("Something went wrong")
        return

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