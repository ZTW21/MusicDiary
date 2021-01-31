from fastapi import FastAPI, Response, Cookie, Request
from jinja2 import Environment, PackageLoader, select_autoescape
import fastapi.templating
import fastapi.staticfiles
from fastapi.responses import HTMLResponse
import spotify, random, string
from starlette.responses import RedirectResponse
from typing import *
from base64 import b64encode
import uvicorn
from dotenv import load_dotenv
import os

async def from_code(
        cls, client: "spotify.Client", code: str, *, redirect_uri: str,
    ):
        """Create a :class:`User` object from an authorization code.

        Parameters
        ----------
        client : :class:`spotify.Client`
            The spotify client to associate the user with.
        code : :class:`str`
            The authorization code to use to further authenticate the user.
        redirect_uri : :class:`str`
            The rediriect URI to use in tandem with the authorization code.
        """
        route = ("POST", "https://accounts.spotify.com/api/token")
        payload = {
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
        }

        client_id = client.http.client_id
        client_secret = client.http.client_secret

        headers = {
            "Authorization": f"Basic {b64encode(':'.join((client_id, client_secret)).encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        raw = await client.http.request(route, headers=headers, params=payload)
        token = raw["access_token"]
        refresh_token = raw["refresh_token"]

        return cls.from_token(client, token, refresh_token)

app = FastAPI()
load_dotenv()
CLI_ID = os.getenv("CLIENT_ID")
CLI_SEC = os.getenv("CLIENT_SECRET")
SPOTIFY_CLIENT = spotify.Client(CLI_ID, CLI_SEC)
REDIRECT_URI: str = 'https://main.d4rziswelfhym.amplifyapp.com/spotify/callback'
OAUTH2_SCOPES: Tuple[str] = ('user-top-read',)
OAUTH2: spotify.OAuth2 = spotify.OAuth2(SPOTIFY_CLIENT.id, REDIRECT_URI, scopes=OAUTH2_SCOPES)
SPOTIFY_USERS: Dict[str, spotify.User] = {}
templates = fastapi.templating.Jinja2Templates(directory="templates")
app.mount("/static",fastapi.staticfiles.StaticFiles(directory="static"),name="static")

@app.get('/spotify/callback')
async def spotify_callback(code : str):
    key = ''.join(random.choice(string.ascii_uppercase) for _ in range(16))
    SPOTIFY_USERS[key] = await from_code(
        spotify.User,
        SPOTIFY_CLIENT,
        code,
        redirect_uri=REDIRECT_URI,
    )
    response = RedirectResponse(url="/")
    response.set_cookie(key="spotify_user_id", value=key)
    return response


@app.get("/")
async def index(request : Request, spotify_user_id : Optional[str] = Cookie(None)):
    print('spotify_user_id:', spotify_user_id)
    if spotify_user_id is None:
        return RedirectResponse(url=OAUTH2.url)
    return templates.TemplateResponse("index.html",{"request" : request})

@app.get("/albums")
def albums(request : Request):
    return templates.TemplateResponse('albums.html',{'request' : request})

@app.get("/diary")
def diary(request : Request):
    return templates.TemplateResponse('diary.html',{'request' : request})