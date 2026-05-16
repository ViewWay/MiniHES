from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.schemas.alarm import AlarmRuleCreate, AlarmRuleUpdate
from app.services import alarm_service

router = APIRouter(prefix="/alarm-rules", tags=["alarm-rules"])


@router.get("")
async def list_alarm_rules(
    db: DbSession = ...,
    _user: CurrentUser = ...,
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    rule_type: str = Query(default=None),
):
    data = await alarm_service.list_alarm_rules(db, page=page, page_size=page_size, rule_type=rule_type)
    return success(data)


@router.post("")
async def create_alarm_rule(body: AlarmRuleCreate, db: DbSession = ..., _user: CurrentUser = ...):
    rule_id = await alarm_service.create_alarm_rule(db, body.model_dump())
    return success({"id": rule_id})


@router.put("/{rule_id}")
async def update_alarm_rule(rule_id: int, body: AlarmRuleUpdate, db: DbSession = ..., _user: CurrentUser = ...):
    await alarm_service.update_alarm_rule(db, rule_id, body.model_dump(exclude_unset=True))
    return success(None)


@router.delete("/{rule_id}")
async def delete_alarm_rule(rule_id: int, db: DbSession = ..., _user: CurrentUser = ...):
    await alarm_service.delete_alarm_rule(db, rule_id)
    return success(None)
