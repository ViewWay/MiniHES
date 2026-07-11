---
name: "source-command-dev"
description: "启动开发服务器 (前端 + 后端)"
---

# source-command-dev

Use this skill when the user asks to run the migrated source command `dev`.

## Command Template

启动 MiniHES 开发环境。

## 执行步骤

1. 后端: `cd backend && uvicorn main:app --reload --port 8000`
2. 前端: `cd frontend && pnpm dev --port 3000`

## 访问地址

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
