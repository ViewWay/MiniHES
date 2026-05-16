"""
通信适配层 - 支持多种通信方式
"""

from .base import CommunicationAdapter, ConnectionConfig
from .cellular import CellularAdapter
from .infrared import InfraredAdapter

__all__ = [
    "CommunicationAdapter",
    "ConnectionConfig",
    "InfraredAdapter",
    "CellularAdapter",
]
