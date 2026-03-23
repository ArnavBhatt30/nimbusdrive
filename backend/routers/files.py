from fastapi import APIRouter, UploadFile, File, Header
from services.s3_service import upload_file, list_files, delete_file, get_download_url
from services.content_extractor import extract_text
from services.database import save_content, delete_content
from routers.auth_router import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])

def get_user_prefix(user: dict) -> str:
    return f"users/{user['id']}/"

@router.post("/upload")
async def upload(file: UploadFile = File(...), authorization: str = Header(None)):
    user = get_current_user(authorization)
    file_bytes = await file.read()
    key = get_user_prefix(user) + file.filename

    result = upload_file(file_bytes, key, file.content_type)

    if result.get("success"):
        content = extract_text(file_bytes, file.filename)
        if content.strip():
            save_content(key, content)

    return result

@router.get("/list")
def get_files(authorization: str = Header(None)):
    user = get_current_user(authorization)
    prefix = get_user_prefix(user)
    result = list_files(prefix=prefix)

    if result.get("success"):
        for f in result["files"]:
            f["filename"] = f["filename"].replace(prefix, "")

    return result

@router.delete("/clear-all")
def clear_all_files(authorization: str = Header(None)):
    user = get_current_user(authorization)
    prefix = get_user_prefix(user)
    result = list_files(prefix=prefix)

    if not result.get("success"):
        return {"success": False, "error": "Could not fetch files"}

    deleted = 0
    for f in result["files"]:
        key = prefix + f["filename"].replace(prefix, "")
        delete_file(key)
        delete_content(key)
        deleted += 1

    return {"success": True, "deleted": deleted}

@router.delete("/{filename}")
def remove_file(filename: str, authorization: str = Header(None)):
    user = get_current_user(authorization)
    key = get_user_prefix(user) + filename
    delete_content(key)
    return delete_file(key)

@router.get("/download/{filename}")
def download_file(filename: str, authorization: str = Header(None)):
    user = get_current_user(authorization)
    key = get_user_prefix(user) + filename
    return get_download_url(key)

@router.get("/preview/{filename}")
def preview_file(filename: str, authorization: str = Header(None)):
    user = get_current_user(authorization)
    key = get_user_prefix(user) + filename
    return get_download_url(key)
