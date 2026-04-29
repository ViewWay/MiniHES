"""
蜂窝网络通信适配器

支持 4G/5G/NB-IoT 通信方式
通过 TCP/IP 连接到远程电表
"""

import socket
import asyncio
from typing import Optional

from .base import CommunicationAdapter, ConnectionConfig, ConnectionType, AdapterException


class CellularAdapter(CommunicationAdapter):
    """
    蜂窝网络通信适配器

    支持通过 4G/5G/NB-IoT 网络连接到电表
    使用 TCP/IP 协议栈
    """

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._socket: Optional[socket.socket] = None

    async def connect(self) -> bool:
        """建立蜂窝网络 TCP 连接"""
        try:
            # 创建 TCP 连接
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.config.address,
                    self.config.port or 4059  # DLMS 默认端口
                ),
                timeout=self.config.timeout
            )

            # 设置 TCP 选项
            sock = self._writer.get_extra_info('socket')
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # 启用 Keep-Alive
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            self._connected = True
            return True

        except (asyncio.TimeoutError, OSError) as e:
            raise AdapterException(f"Failed to connect via cellular: {e}")

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass

        self._reader = None
        self._writer = None
        self._connected = False
        return True

    async def send(self, data: bytes) -> int:
        """发送数据"""
        if not self._connected or not self._writer:
            raise AdapterException("Not connected to cellular adapter")

        try:
            self._writer.write(data)
            await self._writer.drain()
            return len(data)
        except (ConnectionError, OSError) as e:
            self._connected = False
            raise AdapterException(f"Failed to send via cellular: {e}")

    async def receive(self, length: int = None) -> bytes:
        """接收数据"""
        if not self._connected or not self._reader:
            raise AdapterException("Not connected to cellular adapter")

        try:
            if length is None:
                # 读取直到 EOF 或超时
                data = await asyncio.wait_for(
                    self._reader.read(1024),
                    timeout=self.config.timeout
                )
            else:
                data = await asyncio.wait_for(
                    self._reader.readexactly(length),
                    timeout=self.config.timeout
                )
            return data
        except asyncio.IncompleteReadError as e:
            # 返回已读取的数据
            return e.partial
        except asyncio.TimeoutError:
            # 超时返回空数据
            return b""
        except (ConnectionError, OSError) as e:
            self._connected = False
            raise AdapterException(f"Failed to receive via cellular: {e}")

    async def get_adapter_info(self) -> dict:
        """获取适配器信息"""
        # 检测蜂窝网络类型
        conn_type = "cellular"
        if self.config.connection_type == ConnectionType.NBIOT:
            conn_type = "nb-iot"
        elif self.config.connection_type == ConnectionType.CELLULAR_4G:
            conn_type = "4g"
        elif self.config.connection_type == ConnectionType.CELLULAR_5G:
            conn_type = "5g"

        return {
            "type": conn_type,
            "host": self.config.address,
            "port": self.config.port,
            "connected": self._connected
        }
