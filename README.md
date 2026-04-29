# MiniHES

Full-stack application: Nuxt 3 (frontend) + FastAPI (backend).

## 项目结构

```
MiniHES/
├── frontend/              # Nuxt 3 前端
│   ├── pages/            # 页面路由 (文件系统路由)
│   ├── components/       # Vue 组件
│   ├── composables/      # 组合式函数
│   ├── stores/           # Pinia 状态管理
│   ├── server/api/       # 服务端 API 代理
│   ├── types/            # TypeScript 类型
│   └── nuxt.config.ts    # Nuxt 配置
│
└── backend/              # FastAPI 后端
    ├── app/
    │   ├── api/          # API 路由
    │   │   └── v1/
    │   │       ├── endpoints/  # 端点实现
    │   │       └── api.py      # 路由聚合
    │   ├── core/         # 配置、安全、依赖
    │   ├── models/       # SQLAlchemy 模型
    │   ├── schemas/      # Pydantic 模型
    │   ├── services/     # 业务逻辑
    │   └── db/           # 数据库会话
    └── tests/            # 测试
```

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库连接
uvicorn main:app --reload
```

### 前端

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm dev
```

## 开发指南

### 后端开发

**添加新端点:**

1. 在 `backend/app/api/v1/endpoints/` 创建路由文件
2. 在 `backend/app/api/v1/api.py` 注册路由

```python
# endpoints/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def list_users():
    return {"users": []}

# api.py
from app.api.v1.endpoints import users
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

**数据库操作:**

使用 Async SQLAlchemy 进行异步数据库操作，业务逻辑放在 `services/` 目录。

### 前端开发

**添加新页面:**

在 `frontend/pages/` 创建 `.vue` 文件，自动生成路由。

**API 调用:**

使用 Nuxt 服务端 API 路由代理后端请求：

```typescript
// server/api/users.ts
export default defineEventHandler(async () => {
  const config = useRuntimeConfig()
  const response = await fetch(`${config.public.apiBase}/users`)
  return await response.json()
})

// 页面中使用
const { data } = await useFetch('/api/users')
```

**状态管理:**

使用 Pinia stores (`frontend/stores/`)。

## 访问地址

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
# MiniHES
