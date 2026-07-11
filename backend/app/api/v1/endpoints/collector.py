"""采集配置 API — Registry 查询 + OBIS 模板管理。

Registry 查询供前端动态渲染任务创建表单：
  GET /collector/combinations       — 所有 device × category 组合
  GET /collector/schema             — 某组合的 JSON Schema（含 tags 标注）
  GET /collector/devices/{dt}/categories — 某设备类型支持的任务类型

OBIS 模板管理：
  GET /collector/templates          — 模板列表（可按 device_type/task_category 筛选）
  GET /collector/templates/{id}     — 模板详情（含数据点明细）
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.services.collector.bootstrap import register_all
from app.services.collector.registry import registry
from app.services.collector.template_service import (
    get_template_detail,
    list_templates,
)
from app.services.collector.types import DeviceType, TaskCategory

router = APIRouter()

# 启动时注册所有组合
register_all()


# ============================================================
# Registry 查询接口（供前端动态表单）
# ============================================================


@router.get("/collector/combinations")
async def api_list_combinations():
    """列出所有已注册的 device × category 组合"""
    return success(registry.list_combinations())


@router.get("/collector/devices/{device_type}/categories")
async def api_list_categories(device_type: str):
    """列出某设备类型支持的所有任务类型"""
    try:
        dt = DeviceType(device_type)
    except ValueError:
        return success([])
    return success(registry.list_by_device(dt))


@router.get("/collector/schema")
async def api_get_schema(
    device_type: str = Query(..., description="设备类型"),
    task_category: str = Query(..., description="任务类型"),
):
    """返回某组合的 JSON Schema（含字段 tags 标注，供前端动态渲染表单）"""
    try:
        dt = DeviceType(device_type)
        tc = TaskCategory(task_category)
    except ValueError:
        return success(None)

    schema = registry.get_json_schema(dt, tc)
    return success(schema)


# ============================================================
# OBIS 模板管理接口
# ============================================================


@router.get("/collector/templates")
async def api_list_templates(
    db: DbSession = ...,
    device_type: str | None = Query(None, description="按设备类型筛选"),
    task_category: str | None = Query(None, description="按任务类型筛选"),
    _user: CurrentUser = ...,
):
    """模板列表（含每模板的数据点数量）"""
    items = await list_templates(db, device_type=device_type, task_category=task_category)
    return success(items)


@router.get("/collector/templates/{template_id}")
async def api_get_template(
    template_id: int,
    db: DbSession = ...,
    _user: CurrentUser = ...,
):
    """模板详情（含全部数据点明细）"""
    item = await get_template_detail(db, template_id)
    return success(item)
