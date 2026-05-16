from app.core.dependencies import get_current_user  # noqa: F401

# 兼容旧代码引用: from app.core.auth import get_current_user
# 新代码请使用: from app.core.dependencies import CurrentUser, DbSession
