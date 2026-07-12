import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    import aiosmtplib

    _AIOSMTPLIB_AVAILABLE = True
except ImportError:  # aiosmtplib 未安装时优雅降级
    aiosmtplib = None  # type: ignore[assignment]
    MIMEMultipart = None  # type: ignore[assignment]
    MIMEText = None  # type: ignore[assignment]
    _AIOSMTPLIB_AVAILABLE = False
    logger.warning("aiosmtplib 未安装，邮件发送功能不可用")


async def send_email(to: str, subject: str, body: str) -> None:
    """发送邮件。失败时仅记录日志，不抛异常，避免影响主请求。"""
    if not _AIOSMTPLIB_AVAILABLE:
        logger.warning("aiosmtplib 未安装，跳过发送邮件到 %s", to)
        return
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST 未配置，跳过发送邮件到 %s", to)
        return

    try:
        message = MIMEMultipart()
        message["From"] = settings.SMTP_FROM or settings.SMTP_USER
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "html", "utf-8"))

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("邮件已发送至 %s，主题: %s", to, subject)
    except Exception as e:  # noqa: BLE001
        logger.error("发送邮件到 %s 失败: %s", to, e)


async def send_password_reset_email(to: str, reset_token: str, username: str) -> None:
    """构造密码重置链接并发送邮件。"""
    reset_link = f"/reset-password?token={reset_token}"
    subject = f"【{settings.PROJECT_NAME}】密码重置"
    body = (
        f"<p>您好，{username}：</p>"
        f"<p>我们收到了您的密码重置请求。请点击下方链接重置密码（30 分钟内有效）：</p>"
        f'<p><a href="{reset_link}">{reset_link}</a></p>'
        f"<p>如非本人操作，请忽略此邮件。</p>"
        f"<p>{settings.PROJECT_NAME} 团队</p>"
    )
    await send_email(to, subject, body)
