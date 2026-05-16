from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "sys_department"
    __table_args__ = {"comment": "部门表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_department.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    leader: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")

    children: Mapped[list["Department"]] = relationship(backref="parent", remote_side="Department.id")
    users: Mapped[list["User"]] = relationship(back_populates="department")


class User(Base, TimestampMixin):
    __tablename__ = "sys_user"
    __table_args__ = {"comment": "用户表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    avatar: Mapped[str] = mapped_column(String(500), default="")
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_department.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department: Mapped["Department | None"] = relationship(back_populates="users")
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Role(Base, TimestampMixin):
    __tablename__ = "sys_role"
    __table_args__ = {"comment": "角色表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    role_users: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    role_permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class Permission(Base, TimestampMixin):
    __tablename__ = "sys_permission"
    __table_args__ = {"comment": "权限表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(20))  # menu, button, api
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sys_permission.id", ondelete="SET NULL"), nullable=True)
    path: Mapped[str] = mapped_column(String(200), default="")
    icon: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    children: Mapped[list["Permission"]] = relationship(backref="parent", remote_side="Permission.id")
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission", cascade="all, delete-orphan"
    )


class UserRole(Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"), {"comment": "用户角色关联表"})

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_role.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="user_roles")
    role: Mapped["Role"] = relationship(back_populates="role_users")


class RolePermission(Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"), {"comment": "角色权限关联表"})

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_role.id", ondelete="CASCADE"))
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_permission.id", ondelete="CASCADE"))

    role: Mapped["Role"] = relationship(back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(back_populates="role_permissions")
