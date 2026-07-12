"""大屏数据 API 端点。

提供三个大屏页面所需的数据接口：
  GET /screens/overview          — 总览大屏
  GET /screens/project/{id}      — 项目大屏
  GET /screens/meter/{id}        — 电表详情大屏
"""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import BusinessException
from app.core.response import success
from app.services import screen_service

router = APIRouter(prefix="/screens", tags=["screens"])


@router.get("/overview")
async def screen_overview(
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """总览大屏数据。

    数据来源：PG（设备/告警/读数/任务统计），Redis 缓存 30s。
    """
    data = await screen_service.get_overview(db)
    return success(data)


@router.get("/project/{project_id}")
async def screen_project(
    project_id: int,
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """项目大屏数据。

    包含项目维度设备统计、告警数、今日采集量、设备列表。
    """
    data = await screen_service.get_project_screen(db, project_id)
    return success(data)


@router.get("/meter/{meter_id}")
async def screen_meter(
    meter_id: int,
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """单电表大屏详情。

    包含电表元信息、快照状态、最近 10 条读数、最近 5 条告警。
    """
    data = await screen_service.get_meter_detail(db, meter_id)
    if data is None:
        raise BusinessException(code=404, message=f"电表 {meter_id} 不存在")
    return success(data)
