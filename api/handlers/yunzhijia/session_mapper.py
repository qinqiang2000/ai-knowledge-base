"""会话映射管理器 - 管理云之家会话与 Agent 会话的映射关系."""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """会话信息"""
    agent_session_id: str
    last_active: float


class SessionMapper:
    """会话映射管理器

    职责：
    1. 管理 yzj_session_id ↔ agent_session_id 映射
    2. 跟踪会话活动时间
    3. 自动清理超时会话
    """

    def __init__(self, timeout_seconds: int):
        """初始化会话映射器

        Args:
            timeout_seconds: 会话超时时间（秒）
        """
        self.timeout_seconds = timeout_seconds
        self.session_map: Dict[str, SessionInfo] = {}

    def get_or_create(self, yzj_session_id: str) -> Optional[str]:
        """获取有效的 agent_session_id（自动检查超时）

        如果会话存在且未超时，返回 agent_session_id；
        如果会话超时或不存在，返回 None。

        Args:
            yzj_session_id: 云之家会话 ID

        Returns:
            有效的 agent_session_id，或 None（需要创建新会话）
        """
        if yzj_session_id not in self.session_map:
            return None

        session_info = self.session_map[yzj_session_id]
        elapsed = time.time() - session_info.last_active

        if elapsed > self.timeout_seconds:
            # 会话超时，清理
            logger.info(
                f"[SessionMapper] Session timeout: yzj={yzj_session_id}, "
                f"agent={session_info.agent_session_id}, "
                f"inactive={elapsed:.0f}s (threshold={self.timeout_seconds}s)"
            )
            del self.session_map[yzj_session_id]
            return None

        # 会话有效
        return session_info.agent_session_id

    def update_activity(self, yzj_session_id: str, agent_session_id: str):
        """更新会话活动时间

        Args:
            yzj_session_id: 云之家会话 ID
            agent_session_id: Agent 会话 ID
        """
        self.session_map[yzj_session_id] = SessionInfo(
            agent_session_id=agent_session_id,
            last_active=time.time()
        )

    def cleanup_expired(self):
        """清理所有过期会话"""
        current_time = time.time()
        expired_sessions = []

        for yzj_session_id, session_info in self.session_map.items():
            elapsed = current_time - session_info.last_active
            if elapsed > self.timeout_seconds:
                expired_sessions.append(yzj_session_id)

        for yzj_session_id in expired_sessions:
            session_info = self.session_map[yzj_session_id]
            logger.info(
                f"[SessionMapper] Cleaning expired: yzj={yzj_session_id}, "
                f"agent={session_info.agent_session_id}"
            )
            del self.session_map[yzj_session_id]

        if expired_sessions:
            logger.info(f"[SessionMapper] Cleaned {len(expired_sessions)} expired sessions")

    def get_stats(self) -> dict:
        """获取会话统计信息

        Returns:
            统计信息字典，包含会话数量、映射关系和活动时间
        """
        current_time = time.time()
        sessions = []

        for yzj_session_id, session_info in self.session_map.items():
            inactive_seconds = current_time - session_info.last_active
            sessions.append({
                "yzj_session_id": yzj_session_id,
                "agent_session_id": session_info.agent_session_id,
                "inactive_seconds": int(inactive_seconds),
                "will_expire_in": max(0, int(self.timeout_seconds - inactive_seconds))
            })

        return {
            "total_sessions": len(self.session_map),
            "session_timeout_seconds": self.timeout_seconds,
            "sessions": sessions
        }
