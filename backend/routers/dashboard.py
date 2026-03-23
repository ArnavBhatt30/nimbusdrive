from fastapi import APIRouter, Header
from services.s3_service import list_files
from routers.auth_router import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_file_type(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg','jpeg','png','gif','webp','svg']: return 'Images'
    if ext in ['mp4','mov','avi','mkv','webm']:         return 'Videos'
    if ext in ['mp3','wav','ogg','flac']:               return 'Audio'
    if ext in ['pdf','doc','docx','txt','ppt','pptx']:  return 'Documents'
    if ext in ['py','js','html','css','json','ts']:     return 'Code'
    if ext in ['zip','rar','7z','tar','gz']:            return 'Archives'
    if ext in ['xls','xlsx','csv']:                     return 'Spreadsheets'
    return 'Other'

@router.get("/stats")
def get_stats(authorization: str = Header(None)):
    user = get_current_user(authorization)
    prefix = f"users/{user['id']}/"

    response = list_files(prefix=prefix)
    if not response['success']:
        return {"success": False, "error": "Could not fetch files"}

    files = response['files']

    # Strip prefix for display
    for f in files:
        f["filename"] = f["filename"].replace(prefix, "")

    total_files = len(files)
    total_size  = sum(f['size'] for f in files)

    type_breakdown = {}
    for f in files:
        ftype = get_file_type(f['filename'])
        type_breakdown[ftype] = type_breakdown.get(ftype, 0) + 1

    recent  = sorted(files, key=lambda x: x['last_modified'], reverse=True)[:5]
    largest = sorted(files, key=lambda x: x['size'],          reverse=True)[:3]

    return {
        "success": True,
        "total_files": total_files,
        "total_size": total_size,
        "total_size_mb": round(total_size / 1048576, 2),
        "type_breakdown": type_breakdown,
        "recent_uploads": recent,
        "largest_files": largest
    }
