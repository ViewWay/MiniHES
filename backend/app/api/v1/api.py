from fastapi import APIRouter

from app.api.v1.endpoints import (
    alarm_rules,
    alarms,
    analysis,
    auth,
    borrows,
    defects,
    departments,
    health,
    menus,
    menu,
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

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(upload.router)
api_router.include_router(menu.router)
api_router.include_router(projects.router)
api_router.include_router(meters.router)
api_router.include_router(tasks.router)
api_router.include_router(task_logs.router)
api_router.include_router(alarms.router)
api_router.include_router(alarm_rules.router)
api_router.include_router(analysis.router)
api_router.include_router(tests.router)
api_router.include_router(defects.router)
api_router.include_router(borrows.router)
api_router.include_router(system.router)
api_router.include_router(departments.router)
api_router.include_router(menus.router)
api_router.include_router(roles.router)
api_router.include_router(reference.router)
