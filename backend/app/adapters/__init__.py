"""
通信适配层 - 支持多种通信方式
"""

from .base import CommunicationAdapter, ConnectionConfig
from .infrared import InfraredAdapter
from .cellular import CellularAdapter

__all__ = [
    "CommunicationAdapter",
    "ConnectionConfig",
    "InfraredAdapter",
    "CellularAdapter",
]
