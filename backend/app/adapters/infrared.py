"""
红外通信适配器

用于通过红外接口与电表通信
支持光学探头的串口连接
"""

from typing import Optional

import serial
import serial.asyncio

from .base import AdapterException, CommunicationAdapter, ConnectionConfig


class InfraredAdapter(CommunicationAdapter):
    """
    红外通信适配器

    使用串口连接光学读取探头 (Optical Readout Probe)
    支持标准: IEC 62056-21 (Direct local data exchange)
    """

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._serial: Optional[serial.asyncio.Serial] = None
        self._baud_rate = config.port or 9600
        self._parity = serial.PARITY_NONE
        self._stop_bits = serial.STOPBITS_ONE
        self._data_bits = 8

    async def connect(self) -> bool:
        """建立红外串口连接"""
        try:
            self._serial = serial.asyncio.Serial(
                port=self.config.address,
                baudrate=self._baud_rate,
                parity=self._parity,
                stopbits=self._stop_bits,
                bytesize=self._data_bits,
                timeout=self.config.timeout,
            )
            # 打开串口
            if not self._serial.is_open:
                await self._serial.open_async()

            self._connected = True
            return True

        except serial.SerialException as e:
            raise AdapterException(f"Failed to open infrared port: {e}")

    async def disconnect(self) -> bool:
        """断开连接"""
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._connected = False
            return True
        return False

    async def send(self, data: bytes) -> int:
        """发送数据到红外接口"""
        if not self._connected or not self._serial:
            raise AdapterException("Not connected to infrared adapter")

        try:
            self._serial.write(data)
            await self._serial.drain()
            return len(data)
        except serial.SerialException as e:
            raise AdapterException(f"Failed to send infrared data: {e}")

    async def receive(self, length: int = None) -> bytes:
        """从红外接口接收数据"""
        if not self._connected or not self._serial:
            raise AdapterException("Not connected to infrared adapter")

        try:
            if length is None:
                # 读取所有可用数据
                data = self._serial.read_all()
            else:
                # 读取指定长度
                data = await self._serial.read_async(length)
            return bytes(data)
        except serial.SerialException as e:
            raise AdapterException(f"Failed to receive infrared data: {e}")

    async def get_adapter_info(self) -> dict:
        """获取红外适配器信息"""
        return {
            "type": "infrared",
            "port": self.config.address,
            "baud_rate": self._baud_rate,
            "connected": self._connected,
        }
