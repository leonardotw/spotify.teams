# Use Spotify playing music as Teams Status Message

Just a simple script to update Team´s Personal Status Message.

## Config

The configuration uses two files to load credentials :

### .env

Contains information about Spotify integration:
```
SPOTIPY_CLIENT_ID='your-spotify-client-id'
SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
SPOTIPY_REDIRECT_URI='your-app-redirect-url'
```

You will need to register your app at [My Dashboard](https://developer.spotify.com/dashboard/applications) to get the credentials necessary to make authorized calls (a client id and client secret).

The SPOTIPY_REDIRECT_URI can be set to any valid URI and must be the same in application and Dashboard.

### Azure.json

Contains information about Azure integration:
```
{
    "authority": "https://login.microsoftonline.com/organizations",
    "client_id": "<client_id>",
    "scope": ["Presence.ReadWrite"],
    "userid": "user id "
}
````
The client ID can br obtained by creating a new aplication following `Step 2: Register the sample with your Azure Active Directory tenant`, from : 

[Microsoft Authentication Library (MSAL) for Python - Documentation](https://github.com/Azure-Samples/ms-identity-python-devicecodeflow).

### first run: 

- Spotify: a browser will open to authenticate.

 - Azure: the command-line provides a code and asks the user to to navigate to https://microsoft.com/devicelogin, where the user will be prompted to enter the code.

### Tokens


The tokens will be stored at two separate files:


- .cache -> Spotify
- .cache.azure -> Azure

