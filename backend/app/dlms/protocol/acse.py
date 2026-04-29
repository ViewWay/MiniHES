"""
ACSE (Application Connection Establishment Element) 连接管理

参考标准:
- ISO/IEC 9805-2: Presentation Layer
- IEC 62056-53: DLMS/COSEM Application Layer
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, List


class ACSEException(Exception):
    """ACSE 异常"""
    pass


class AuthenticationMechanism(IntEnum):
    """认证机制"""
    NONE = 0
    LOW_LEVEL = 1
    HIGH_LEVEL = 2
    HIGH_LEVEL_WITH_MD5 = 5
    HIGH_LEVEL_WITH_SHA1 = 6
    HIGH_LEVEL_WITH_SHA256 = 7
    HIGH_LEVEL_WITH_GMAC = 9
    HIGH_LEVEL_WITH_ECDSA = 10


@dataclass
class DLMSConnectionParam:
    """DLMS 连接参数"""
    client_id: int = 16
    server_id: int = 1
    authentication: AuthenticationMechanism = AuthenticationMechanism.NONE
    password: Optional[bytes] = None
    interface: str = "HDLC"  # HDLC, UDP, WRAPPER
    baud_rate: int = 9600


class ACSEManager:
    """ACSE 连接管理器"""

    def __init__(self, params: DLMSConnectionParam):
        self.params = params
        self._connected = False

    async def associate(self) -> bytes:
        """建立应用层连接 (AARQ)"""
        # 简化实现 - 实际需要构建完整的 AARQ APDU
        if not self.params.password:
            return self._build_aarq_no_auth()

        if self.params.authentication == AuthenticationMechanism.LOW_LEVEL:
            return self._build_aarq_low_level()
        else:
            return self._build_aarq_high_level()

    def _build_aarq_no_auth(self) -> bytes:
        """构建无认证 AARQ"""
        # AARQ application-context-name + user-information
        return bytes([
            0x60,  # AARQ tag
            0x1E,  # Length
            0x80, 0x02, 0x07, 0x80,  # application-context-name (DLMS UA)
            0x80, 0x02, 0x07, 0x80,  # authentication-mechanism-name
            0xBE, 0x10, 0x04, 0x0E,  # user-information (calling-AP-title + called-AP-title)
            0x08, self.params.client_id, 0x08, self.params.server_id,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

    def _build_aarq_low_level(self) -> bytes:
        """构建低等级认证 AARQ"""
        password = self.params.password or b""
        return bytes([
            0x60, len(password) + 30,
            0x80, 0x02, 0x07, 0x80,
            0x80, 0x02, 0x07, 0x81,  # Low-level authentication
            0xBE, 0x10, 0x04, 0x0E,
            0x08, self.params.client_id, 0x08, self.params.server_id,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]) + password

    def _build_aarq_high_level(self) -> bytes:
        """构建高等级认证 AARQ (LS=0)"""
        # 高等级认证使用 HLS 机制，需要密码和随机数
        password = self.params.password or b""
        return bytes([
            0x60, len(password) + 30,
            0x80, 0x02, 0x07, 0x80,
            0x80, 0x02, 0x07, 0x82,  # High-level authentication
            0xBE, 0x10, 0x04, 0x0E,
            0x08, self.params.client_id, 0x08, self.params.server_id,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]) + password

    async def release(self) -> bytes:
        """释放连接 (RLREQ)"""
        return bytes([0x62, 0x02, 0x80, 0x00])  # RLREQ normal

    async def parse_associate_response(self, data: bytes) -> bool:
        """解析连接响应 (AARE)"""
        if not data or data[0] != 0x62:  # AARE tag
            raise ACSEException("Invalid AARE response")

        # data[3] = result: 0=accepted, other=rejected
        result = data[3]
        if result != 0:
            raise ACSEException(f"Connection rejected with code: {result}")

        self._connected = True
        return True

    async def parse_release_response(self, data: bytes) -> bool:
        """解析释放响应 (RLRE)"""
        self._connected = False
        return data[0] == 0x64  # RLRE tag

    @property
    def is_connected(self) -> bool:
        """连接状态"""
        return self._connected
