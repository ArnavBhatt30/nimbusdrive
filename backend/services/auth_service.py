import sqlite3
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nimbusdrive-super-secret-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT,
            is_oauth   INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "email": row[2], "password": row[3]}
    return None

def get_user_by_id(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "email": row[2]}
    return None

def get_or_create_oauth_user(email: str, username: str):
    """Get existing user or create new one for OAuth login"""
    user = get_user_by_email(email)
    if user:
        return user
    # Create new OAuth user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Handle duplicate username
    base_username = username
    counter = 1
    while True:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            break
        username = f"{base_username}{counter}"
        counter += 1
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, is_oauth) VALUES (?, ?, ?, 1)",
            (username, email, "", )
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "username": username, "email": email}
    except Exception as e:
        conn.close()
        return None

def register_user(username: str, email: str, password: str):
    if get_user_by_email(email):
        return {"success": False, "error": "Email already registered"}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Username already taken"}
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        token = create_token(user_id)
        return {"success": True, "token": token, "username": username, "email": email}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def login_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return {"success": False, "error": "Invalid email or password"}
    token = create_token(user['id'])
    return {"success": True, "token": token, "username": user['username'], "email": user['email']}

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Normal login token — has user_id
        if "user_id" in payload:
            return get_user_by_id(payload["user_id"])
        # OAuth token — has email and username
        elif "email" in payload:
            email = payload["email"]
            username = payload.get("username", email.split("@")[0])
            return get_or_create_oauth_user(email, username)
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
