import os
import urllib.parse
import secrets
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi import APIRouter
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY           = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "change_this_secret"))
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"
REDIRECT_URI     = "http://127.0.0.1:8000/auth/google/callback"

state_store = {}
pending_tokens = {}

def create_token(data: dict, expires_hours: int = 72) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.get("/auth/google")
async def google_login():
    state = secrets.token_urlsafe(32)
    state_store[state] = datetime.utcnow()
    params = urllib.parse.urlencode({
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "offline",
        "prompt":        "select_account",
    })
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}")

@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    print(f"[CALLBACK] ALL PARAMS: {dict(request.query_params)}")
    print(f"[CALLBACK] code={code}, state={state}, error={error}")

    if error:
        return HTMLResponse(f"""<script>window.location.href='{FRONTEND_URL}/login.html?oauth_error={urllib.parse.quote(error)}';</script>""")

    if not code or not state:
        return HTMLResponse(f"""<script>window.location.href='{FRONTEND_URL}/login.html?oauth_error=Missing+code+or+state';</script>""")

    if state not in state_store:
        print(f"[CALLBACK] State not found! Known states: {list(state_store.keys())}")
        return HTMLResponse(f"""<script>window.location.href='{FRONTEND_URL}/login.html?oauth_error=Invalid+state';</script>""")

    del state_store[state]

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        token_data = token_resp.json()
        print(f"[CALLBACK] Token response: {token_data.get('error', 'OK')}")

        access_token = token_data.get("access_token")
        if not access_token:
            return HTMLResponse(f"""<script>window.location.href='{FRONTEND_URL}/login.html?oauth_error=No+access+token';</script>""")

        user_resp = await client.get(GOOGLE_USERINFO, headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_resp.json()
        print(f"[CALLBACK] User info: {user_info.get('email')}")

    email = user_info.get("email", "")
    name  = user_info.get("name") or user_info.get("given_name") or email.split("@")[0]

    app_token = create_token({"email": email, "username": name})

    temp_key = secrets.token_urlsafe(32)
    pending_tokens[temp_key] = {
        "token":    app_token,
        "username": name,
        "email":    email,
        "exp":      datetime.utcnow() + timedelta(seconds=120)
    }

    redirect_url = f"{FRONTEND_URL}/login.html?oauth_key={temp_key}"
    print(f"[CALLBACK] Redirecting to: {redirect_url[:60]}...")
    return HTMLResponse(f"""<!DOCTYPE html><html><body>
<script>window.location.href='{redirect_url}';</script>
</body></html>""")

@router.get("/auth/oauth-token")
async def get_oauth_token(key: str):
    data = pending_tokens.pop(key, None)
    if not data or datetime.utcnow() > data["exp"]:
        return JSONResponse({"success": False, "error": "Invalid or expired key"}, status_code=400)
    return JSONResponse({"success": True, "token": data["token"], "username": data["username"], "email": data["email"]})
