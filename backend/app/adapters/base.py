"""
通信适配器抽象基类

所有通信适配器都必须继承此类并实现核心方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class ConnectionType(IntEnum):
    """通信类型"""

    INFRARED = 1
    CELLULAR_4G = 2
    CELLULAR_5G = 3
    NBIOT = 4
    MBUS = 5
    LORAWAN = 6
    G3_PLC = 7
    TCP_IP = 8
    UDP_IP = 9


@dataclass
class ConnectionConfig:
    """连接配置"""

    connection_type: ConnectionType
    address: str  # IP地址、串口等
    port: Optional[int] = None  # 端口、波特率等
    timeout: int = 30  # 超时时间(秒)
    retry_count: int = 3
    retry_delay: int = 1

    # 扩展配置参数
    extra_params: dict = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class AdapterException(Exception):  # noqa: N818
    """适配器异常"""

    pass


class CommunicationAdapter(ABC):
    """
    通信适配器抽象基类

    定义所有通信适配器的通用接口
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connected = False
        self._connection = None

    @property
    def is_connected(self) -> bool:
        """连接状态"""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """
        建立连接

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开连接

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    async def send(self, data: bytes) -> int:
        """
        发送数据

        Args:
            data: 要发送的字节数据

        Returns:
            int: 发送的字节数

        Raises:
            AdapterException: 发送失败
        """
        pass

    @abstractmethod
    async def receive(self, length: int = None) -> bytes:
        """
        接收数据

        Args:
            length: 要接收的字节数，None表示接收所有可用数据

        Returns:
            bytes: 接收到的数据

        Raises:
            AdapterException: 接收失败
        """
        pass

    async def send_and_receive(self, data: bytes, response_length: int = None, timeout: int = None) -> bytes:
        """
        发送并接收数据的便捷方法

        Args:
            data: 要发送的数据
            response_length: 期望接收的长度
            timeout: 超时时间

        Returns:
            bytes: 接收到的响应数据
        """
        await self.send(data)
        return await self.receive(response_length)

    async def reconnect(self) -> bool:
        """
        重新连接

        Returns:
            bool: 重连是否成功
        """
        await self.disconnect()
        return await self.connect()

    @abstractmethod
    async def get_adapter_info(self) -> dict:
        """
        获取适配器信息

        Returns:
            dict: 适配器信息
        """
        pass
