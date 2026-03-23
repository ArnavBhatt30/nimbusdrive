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

# ── Init DB ──
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Helpers ──
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

# ── Register ──
def register_user(username: str, email: str, password: str):
    # Check if email already exists
    if get_user_by_email(email):
        return {"success": False, "error": "Email already registered"}

    # Check username
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Username already taken"}

    # Hash password
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

# ── Login ──
def login_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "Invalid email or password"}

    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return {"success": False, "error": "Invalid email or password"}

    token = create_token(user['id'])
    return {
        "success": True,
        "token": token,
        "username": user['username'],
        "email": user['email']
    }

# ── JWT ──
def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = get_user_by_id(payload["user_id"])
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
