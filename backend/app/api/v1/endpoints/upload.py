import os
import uuid

from fastapi import APIRouter, File, UploadFile

from app.core.dependencies import CurrentUser
from app.core.response import success

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")


@router.post("")
async def upload_file(_user: CurrentUser = ..., file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return success(None)

    with open(filepath, "wb") as f:
        f.write(content)

    return success({"url": f"/uploads/{filename}", "filename": file.filename})
