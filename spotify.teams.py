import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv
import requests
import msal
import sys, os 
import json
import logging
import atexit
from datetime import datetime, timedelta, timezone


dotenv.load_dotenv() # Load Spotify Credentials
config = json.load(open('Azure.json')) #Load Azure Credentials

# .env format:
# SPOTIPY_CLIENT_ID='your-spotify-client-id'
# SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
# SPOTIPY_REDIRECT_URI='your-app-redirect-url'

# Azure.json format:
# {
#     "authority": "https://login.microsoftonline.com/organizations",
#     "client_id": "<client_id>",
#     "scope": ["Presence.ReadWrite"],
#     "userid": "user id "
# }

TeamsSetEndpoint = "https://graph.microsoft.com/beta/users/%s/presence/setStatusMessage" % config["userid"]
TeamsGetEndpoint = "https://graph.microsoft.com/beta/users/%s/presence" % config["userid"]

# Optional logging
logging.basicConfig(filename='spotify.log',level=logging.ERROR)  # Enable DEBUG log for entire script

#Spotify

scope = "user-read-currently-playing"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
cplay = sp.current_user_playing_track()
try:
    if (cplay['is_playing'] == True):
        MessageMusic = "Ouvindo: %s - %s" % (cplay['item']['artists'][0]['name'], cplay['item']['name'])
    else:
        MessageMusic = None
except:
    MessageMusic = None

#Azure

cache = msal.SerializableTokenCache()
if os.path.exists(".cache.azure"):
    cache.deserialize(open(".cache.azure", "r").read())
atexit.register(lambda:
    open(".cache.azure", "w").write(cache.serialize())
    # Hint: The following optional line persists only when state changed
    if cache.has_state_changed else None
    )


# Create a preferably long-lived app instance which maintains a token cache.
app = msal.PublicClientApplication(
    config["client_id"], authority=config["authority"],
    token_cache= cache  # Default cache is in memory only.
                       # You can learn how to use SerializableTokenCache from
                       # https://msal-python.readthedocs.io/en/latest/#msal.SerializableTokenCache
    )

# The pattern to acquire a token looks like this.
result = None

# Note: If your device-flow app does not have any interactive ability, you can
#   completely skip the following cache part. But here we demonstrate it anyway.
# We now check the cache to see if we have some end users signed in before.
accounts = app.get_accounts()
if accounts:
    logging.info("Account(s) exists in cache, probably with token too. Let's try.")
    #print("Pick the account you want to use to proceed:")
    #for a in accounts:
        #print(a["username"])
    # Assuming the end user chose this one
    chosen = accounts[0]
    # Now let's try to find a token in cache for this account
    result = app.acquire_token_silent(config["scope"], account=chosen)

if not result:
    logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

    flow = app.initiate_device_flow(scopes=config["scope"])
    if "user_code" not in flow:
        raise ValueError(
            "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    print(flow["message"])
    sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

    # Ideally you should wait here, in order to save some unnecessary polling
    # input("Press Enter after signing in from another device to proceed, CTRL+C to abort.")

    result = app.acquire_token_by_device_flow(flow)  # By default it will block
        # You can follow this instruction to shorten the block time
        #    https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
        # or you may even turn off the blocking behavior,
        # and then keep calling acquire_token_by_device_flow(flow) in your own customized loop.

if "access_token" in result:
    print("Token OK")
else:
    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id"))  # You may need this when reporting a bug

# Update Message

if ((result["access_token"]) and (MessageMusic)):

    #Set and format ExpirityDateTime
    now = datetime.now(timezone.utc)
    TimeRemain= cplay['item']['duration_ms'] - cplay['progress_ms']
    TimeEnd = now + timedelta(milliseconds = TimeRemain)
    #Set Json
    MusicJson = {
    "statusMessage": {
        "message": {
            "content": MessageMusic  ,
            "contentType": "text"
        },
        "expiryDateTime": {
            "dateTime": TimeEnd.isoformat(),
            "timeZone": "UTC"
        }
    }
    }
    #Set Status message
    set_message = requests.post( 
        TeamsSetEndpoint, json = MusicJson,
        headers={'Authorization': 'Bearer ' + result['access_token']},
        )
    #Get Status Message
    graph_data = requests.get(  
        TeamsGetEndpoint,
        headers={'Authorization': 'Bearer ' + result['access_token']},
        )
