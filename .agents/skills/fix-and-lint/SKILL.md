---
name: fix-and-lint
description: |
  修复代码格式和 lint 问题。当用户在提交前需要修复代码风格、
  排查 lint 错误、或说 "fix"、"格式化"、"lint" 时激活。
---

# Fix and Lint

## 何时使用

- 提交前修复代码格式
- lint 检查有报错
- 用户说 "fix"、"格式化"、"lint 修复"

## 后端 (Python)

### 步骤

```bash
# 1. 格式化
cd backend && uv run ruff format .

# 2. Lint 修复
cd backend && uv run ruff check --fix .

# 3. 检查剩余问题
cd backend && uv run ruff check .
```

### 常见问题修复

| 问题 | 修复方式 |
|------|---------|
| 未使用的导入 | `ruff check --fix` 自动移除 |
| 行过长 | `ruff format` 自动换行 |
| 导入顺序 | `ruff check --fix` 自动排序 |
| 类型注解缺失 | 手动添加 |

### 验证

```bash
# 确保修复后测试仍通过
cd backend && uv run pytest
```

## 前端 (TypeScript/Vue)

### 步骤

```bash
# 1. 格式化
cd frontend && pnpm run format

# 2. Lint 修复
cd frontend && pnpm run lint:fix

# 3. 检查剩余问题
cd frontend && pnpm run lint
```

## 数据库迁移检查

如果修改了 model 文件：

```bash
# 检查是否有未应用的迁移
cd backend && uv run alembic check

# 生成迁移（如有模型变更）
cd backend && uv run alembic revision --autogenerate -m "描述"
```

## 输出

修复完成后报告：
1. 格式化了哪些文件
2. 修复了哪些 lint 问题
3. 仍需手动修复的问题（如有）
4. 测试是否通过
