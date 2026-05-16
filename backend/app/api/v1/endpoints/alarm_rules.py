from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.auth import get_current_user
from app.core.database import AsyncSessionLocal as async_session
from app.core.response import success, fail
from app.models.alarm import AlarmRule

router = APIRouter(prefix="/alarm-rules", tags=["alarm-rules"])


@router.get("")
async def list_alarm_rules(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    rule_type: str = Query(default=None),
    _=Depends(get_current_user),
):
    async with async_session() as session:
        stmt = select(AlarmRule)
        count_stmt = select(func.count()).select_from(AlarmRule)

        if rule_type:
            stmt = stmt.where(AlarmRule.rule_type == rule_type)
            count_stmt = count_stmt.where(AlarmRule.rule_type == rule_type)

        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(AlarmRule.id).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
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
async def create_alarm_rule(body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        rule = AlarmRule(**body)
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return success({"id": rule.id})


@router.put("/{rule_id}")
async def update_alarm_rule(rule_id: int, body: dict, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return fail(code=10001, message="告警规则不存在", status=404)
        for key, value in body.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        await session.commit()
        return success(None)


@router.delete("/{rule_id}")
async def delete_alarm_rule(rule_id: int, _=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return fail(code=10001, message="告警规则不存在", status=404)
        await session.delete(rule)
        await session.commit()
        return success(None)
