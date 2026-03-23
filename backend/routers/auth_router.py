from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from services.auth_service import register_user, login_user, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterBody(BaseModel):
    username: str
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(body: RegisterBody):
    if len(body.username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters"}
    if len(body.password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}
    return register_user(body.username, body.email, body.password)

@router.post("/login")
def login(body: LoginBody):
    return login_user(body.email, body.password)

@router.get("/me")
def me(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"success": True, "user": user}

# ── Reusable dependency ──
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
