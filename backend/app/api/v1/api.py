from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    alarm_rules,
    alarms,
    analysis,
    auth,
    borrows,
    collector,
    defects,
    departments,
    health,
    menu,
    menus,
    meters,
    projects,
    reference,
    roles,
    system,
    task_logs,
    tasks,
    tests,
    upload,
    user,
)
from app.core.dependencies import require_permission

api_router = APIRouter()

# 公开接口（无需权限校验）
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(upload.router)
api_router.include_router(menu.router)

# 采集配置 Registry 查询（公开，前端表单渲染需要）
api_router.include_router(collector.router, tags=["collector"])

# 受保护接口（菜单级权限校验，super 角色豁免）
api_router.include_router(projects.router, dependencies=[Depends(require_permission("projects"))])
api_router.include_router(reference.router, dependencies=[Depends(require_permission("projects"))])
api_router.include_router(meters.router, dependencies=[Depends(require_permission("devices"))])
api_router.include_router(borrows.router, dependencies=[Depends(require_permission("devices"))])
api_router.include_router(tasks.router, dependencies=[Depends(require_permission("tasks"))])
api_router.include_router(task_logs.router, dependencies=[Depends(require_permission("tasks"))])
api_router.include_router(alarms.router, dependencies=[Depends(require_permission("alarms"))])
api_router.include_router(alarm_rules.router, dependencies=[Depends(require_permission("alarms"))])
api_router.include_router(analysis.router, dependencies=[Depends(require_permission("analysis"))])
api_router.include_router(tests.router, dependencies=[Depends(require_permission("system"))])
api_router.include_router(defects.router, dependencies=[Depends(require_permission("system"))])
api_router.include_router(system.router, dependencies=[Depends(require_permission("system"))])
api_router.include_router(departments.router, dependencies=[Depends(require_permission("system"))])
api_router.include_router(menus.router, dependencies=[Depends(require_permission("system"))])
api_router.include_router(roles.router, dependencies=[Depends(require_permission("system"))])
