from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from routers.files import router as files_router
from routers.ai_search import router as search_router
from routers.dashboard import router as dashboard_router
from routers.auth_router import router as auth_router
import os

app = FastAPI(title="NimbusDrive API", version="2.0.0")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "fallback_secret"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(files_router)
app.include_router(search_router)
app.include_router(dashboard_router)

@app.get("/health")
def health():
    return {"status": "healthy"}

# Frontend path — works both locally and on Render
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_path = os.path.abspath(frontend_path)

app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
