import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.mongo import close_mongo

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info("MiniHES 启动中...")
    try:
        from app.services.scheduler import init_scheduler

        init_scheduler()
        logger.info("任务调度器已启动")
    except Exception as e:
        logger.warning("任务调度器启动失败（非致命）: %s", e)

    yield

    # 关闭：停止调度器 → 清理数据库连接池和 MongoDB 客户端
    try:
        from app.services.scheduler import shutdown_scheduler

        await shutdown_scheduler()
    except Exception:
        pass
    await engine.dispose()
    await close_mongo()
    logger.info("MiniHES 已关闭，资源已清理")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "MiniHES API is running"}
