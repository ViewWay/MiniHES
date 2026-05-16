from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.alarm import AlarmRule

router = APIRouter(prefix="/alarm-rules", tags=["alarm-rules"])


@router.get("")
async def list_alarm_rules(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    rule_type: str = Query(default=None),
):
    stmt = select(AlarmRule)
    count_stmt = select(func.count()).select_from(AlarmRule)

    if rule_type:
        stmt = stmt.where(AlarmRule.rule_type == rule_type)
        count_stmt = count_stmt.where(AlarmRule.rule_type == rule_type)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(AlarmRule.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rules = result.scalars().all()

    items = [
        {
            "id": r.id,
            "rule_name": r.rule_name,
            "rule_type": r.rule_type,
            "point_code": r.point_code,
            "condition_config": r.condition_config,
            "severity": r.severity,
            "is_enabled": r.is_enabled,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        }
        for r in rules
    ]
    return success({"items": items, "total": total})


@router.post("")
async def create_alarm_rule(body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    rule = AlarmRule(**body)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return success({"id": rule.id})


@router.put("/{rule_id}")
async def update_alarm_rule(rule_id: int, body: dict, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None)
    for key, value in body.items():
        if hasattr(rule, key):
            setattr(rule, key, value)
    await db.commit()
    return success(None)


@router.delete("/{rule_id}")
async def delete_alarm_rule(rule_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    result = await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return success(None)
    await db.delete(rule)
    await db.commit()
    return success(None)
