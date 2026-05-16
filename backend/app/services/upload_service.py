from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.meter import Meter, MeterAttachment

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    # Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    # Documents
    ".pdf",
    # Excel
    ".xls",
    ".xlsx",
    ".csv",
}


def _attachment_to_dict(a: MeterAttachment) -> dict:
    """Convert a MeterAttachment ORM object to a plain dict."""
    return {
        "id": a.id,
        "meter_id": a.meter_id,
        "filename": a.filename,
        "file_path": a.file_path,
        "size": a.size,
        "uploaded_by": a.uploaded_by,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else None,
    }


def _validate_file(filename: str, size: int) -> None:
    """Validate file extension and size."""
    if not filename:
        raise BusinessException(code=400, message="文件名不能为空")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{ext}" not in ALLOWED_EXTENSIONS:
        raise BusinessException(
            code=400,
            message=f"不支持的文件类型: .{ext}，允许类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    if size > MAX_FILE_SIZE:
        raise BusinessException(code=400, message="文件大小不能超过10MB")


async def upload_file(
    db: AsyncSession,
    *,
    meter_id: int,
    filename: str,
    file_path: str,
    size: int = 0,
    uploaded_by: int | None = None,
) -> dict:
    """Upload an attachment for a meter."""
    meter = await db.get(Meter, meter_id)
    if not meter:
        raise BusinessException(code=404, message="样机不存在")

    _validate_file(filename, size)

    attachment = MeterAttachment(
        meter_id=meter_id,
        filename=filename,
        file_path=file_path,
        size=size,
        uploaded_by=uploaded_by,
    )
    db.add(attachment)
    await db.flush()
    return {"id": attachment.id, **_attachment_to_dict(attachment)}


async def list_attachments(db: AsyncSession, meter_id: int) -> list[dict]:
    """List all attachments for a meter."""
    result = await db.execute(
        select(MeterAttachment).where(MeterAttachment.meter_id == meter_id).order_by(MeterAttachment.id.desc())
    )
    return [_attachment_to_dict(a) for a in result.scalars().all()]


async def delete_attachment(db: AsyncSession, attachment_id: int) -> bool:
    """Delete an attachment. Returns True if deleted."""
    attachment = await db.get(MeterAttachment, attachment_id)
    if not attachment:
        raise BusinessException(code=404, message="附件不存在")
    await db.delete(attachment)
    return True
