import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File

from app.core.auth import get_current_user
from app.core.response import success, fail

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")


@router.post("")
async def upload_file(file: UploadFile = File(...), _=Depends(get_current_user)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return fail(code=10001, message="文件大小不能超过10MB", status=400)

    with open(filepath, "wb") as f:
        f.write(content)

    return success({"url": f"/uploads/{filename}", "filename": file.filename})
