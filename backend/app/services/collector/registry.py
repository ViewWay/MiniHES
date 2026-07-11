"""配置注册表 — 每个 device × category 组合注册一个 Pydantic schema + 默认值。

启动时 bootstrap.register_all() 注册所有组合，
task_service 创建/更新任务时调用 registry.validate_config() 校验配置。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type

from pydantic import BaseModel

from .types import VALID_COMBINATIONS, DeviceType, TaskCategory


@dataclass
class ConfigRegistration:
    """一个 device × category 组合的注册信息"""

    device_type: DeviceType
    task_category: TaskCategory
    config_schema: Type[BaseModel]
    defaults: dict[str, Any] = field(default_factory=dict)
    obis_template_name: str | None = None
    description: str = ""


class ConfigRegistry:
    """配置注册表 — 启动时注册所有 device × category 组合"""

    def __init__(self) -> None:
        self._registrations: dict[tuple[DeviceType, TaskCategory], ConfigRegistration] = {}

    def register(self, reg: ConfigRegistration) -> None:
        """注册一个组合"""
        key = (reg.device_type, reg.task_category)
        if key not in VALID_COMBINATIONS:
            raise ValueError(f"无效的设备×任务组合: {reg.device_type} × {reg.task_category}")
        self._registrations[key] = reg

    def get(self, device_type: DeviceType, task_category: TaskCategory) -> ConfigRegistration | None:
        """查找注册信息"""
        return self._registrations.get((device_type, task_category))

    def validate_config(self, device_type: DeviceType, task_category: TaskCategory, raw: dict) -> BaseModel:
        """根据组合查找 schema 并校验 + 填充默认值。

        用户传入的 raw 会覆盖 defaults，最终通过 Pydantic 校验。
        """
        reg = self.get(device_type, task_category)
        if reg is None:
            raise ValueError(
                f"不支持的组合: {device_type} × {task_category}，" f"请检查 device_type 和 task_category 是否正确"
            )
        merged = {**reg.defaults, **raw}
        return reg.config_schema(**merged)

    def get_json_schema(self, device_type: DeviceType, task_category: TaskCategory) -> dict | None:
        """返回该组合的 JSON Schema（含字段 tags 标注，供前端动态渲染表单）"""
        reg = self.get(device_type, task_category)
        if reg is None:
            return None
        return reg.config_schema.model_json_schema()

    def list_combinations(self) -> list[dict]:
        """列出所有已注册组合（供前端选择设备/任务类型）"""
        return [
            {
                "device_type": r.device_type.value,
                "task_category": r.task_category.value,
                "description": r.description,
                "obis_template_name": r.obis_template_name,
            }
            for r in self._registrations.values()
        ]

    def list_by_device(self, device_type: DeviceType) -> list[dict]:
        """列出某设备类型支持的所有任务类型"""
        return [
            {
                "task_category": r.task_category.value,
                "description": r.description,
                "obis_template_name": r.obis_template_name,
            }
            for key, r in self._registrations.items()
            if key[0] == device_type
        ]


# 全局单例
registry = ConfigRegistry()
