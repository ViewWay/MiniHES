"""
APDU (Application Protocol Data Unit) 编解码实现

参考标准:
- IEC 62056-53: DLMS/COSEM Application Layer
- IEC 62056-46: DLMS/COSEM HDLC Protocol
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class DLMSCommand(IntEnum):
    """DLMS 命令码"""
    GET_REQUEST = 1
    GET_RESPONSE = 8
    SET_REQUEST = 2
    SET_RESPONSE = 9
    ACTION_REQUEST = 3
    ACTION_RESPONSE = 10
    GLO_GET_REQUEST = 192
    GLO_GET_RESPONSE = 199
    GLO_SET_REQUEST = 193
    GLO_SET_RESPONSE = 200


class DLMSException(Exception):
    """DLMS 协议异常"""
    pass


@dataclass
class OBISCode:
    """
    OBIS (Object Identification System) 码

    格式: A-B:C.D.E[.F]
    - A: 逻辑设备 (0=未定义, 1=网关)
    - B: 通道 (0-255)
    - C: 接口类别 (IEC 62056-62)
    - D: 测量类型
    - E: 通道/相序
    - F: 类型/其他 (0-255)
    """
    a: int = 1
    b: int = 0
    c: int = 0
    d: int = 0
    e: int = 0
    f: int = 255

    def __str__(self) -> str:
        return f"{self.a}.{self.b}:{self.c}.{self.d}.{self.e}.{self.f}"

    @classmethod
    def from_string(cls, code: str) -> "OBISCode":
        """从字符串解析 OBIS 码"""
        parts = code.replace(":", ".").split(".")
        if len(parts) != 6:
            raise DLMSException(f"Invalid OBIS code format: {code}")
        return cls(*map(int, parts))


@dataclass
class APDURequest:
    """APDU 请求数据结构"""
    command: DLMSCommand
    invoke_id: int
    obis: OBISCode
    attribute: int = 1

    def encode(self) -> bytes:
        """编码为字节序列"""
        # 简化实现，实际需要按照 DLMS 编码规则
        return bytes([
            self.command,
            self.invoke_id & 0xFF,
            self.obis.a, self.obis.b, self.obis.c,
            self.obis.d, self.obis.e, self.obis.f,
            self.attribute
        ])


@dataclass
class APDUResponse:
    """APDU 响应数据结构"""
    command: DLMSCommand
    invoke_id: int
    status: int
    data: Optional[bytes] = None

    @classmethod
    def decode(cls, data: bytes) -> "APDUResponse":
        """从字节序列解码"""
        if len(data) < 3:
            raise DLMSException("Invalid APDU response length")
        return cls(
            command=DLMSCommand(data[0]),
            invoke_id=data[1],
            status=data[2],
            data=data[3:] if len(data) > 3 else None
        )


class APDUEncoder:
    """APDU 编码器"""

    @staticmethod
    def build_get_request(obis: str, attribute: int = 1) -> bytes:
        """构建 Get-Request APDU"""
        obis_code = OBISCode.from_string(obis)
        request = APDURequest(
            command=DLMSCommand.GET_REQUEST,
            invoke_id=1,
            obis=obis_code,
            attribute=attribute
        )
        return request.encode()

    @staticmethod
    def parse_response(data: bytes) -> APDUResponse:
        """解析响应 APDU"""
        return APDUResponse.decode(data)
