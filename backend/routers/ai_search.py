from fastapi import APIRouter, Header
from pydantic import BaseModel
from services.s3_service import list_files
from services.gemini_service import search_files
from services.database import get_all_contents
from routers.auth_router import get_current_user

router = APIRouter(prefix="/search", tags=["AI Search"])

class SearchQuery(BaseModel):
    query: str

@router.post("/")
def ai_search(search: SearchQuery, authorization: str = Header(None)):
    user = get_current_user(authorization)
    prefix = f"users/{user['id']}/"

    files_response = list_files(prefix=prefix)
    if not files_response['success']:
        return {"success": False, "error": "Could not fetch files"}

    # Strip prefix from display names
    files = files_response['files']
    for f in files:
        f["filename"] = f["filename"].replace(prefix, "")

    db_contents = get_all_contents()
    return search_files(search.query, files, db_contents)
