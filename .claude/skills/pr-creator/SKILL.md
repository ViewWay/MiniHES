---
name: pr-creator
description: |
  创建 Pull Request。当用户说 "创建 PR"、"提 PR"、"提交合并请求" 时激活。
  确保遵循 conventional commit、模板规范、安全护栏。
---

# PR Creator

## 何时使用

- 用户说 "创建 PR"、"提 PR"、"merge request"
- 完成功能开发准备提交

## 工作流

### 1. 分支安全检查

```bash
# 确认不在 main 分支
git branch --show-current
```

**如果当前在 main**，必须先创建新分支：
```bash
git checkout -b feat/描述性名称
```

**禁止直接 push main。**

### 2. 提交变更

```bash
# 检查未提交的变更
git status

# 暂存并提交
git add .
git commit -m "type(scope): description"
```

### Commit 格式

遵循 Conventional Commits：

| Type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(collector): add DLMS task scheduler` |
| `fix` | Bug 修复 | `fix(meter): resolve serial number unique constraint` |
| `docs` | 文档 | `docs(api): update meter endpoint docs` |
| `refactor` | 重构 | `refactor(schemas): simplify response models` |
| `test` | 测试 | `test(task): add task service unit tests` |
| `chore` | 杂项 | `chore(deps): update sqlalchemy to 2.0.36` |

### 3. Preflight 检查

```bash
# 后端
cd backend && uv run ruff check . && uv run pytest

# 前端（如有前端变更）
cd frontend && pnpm run lint && pnpm run build
```

检查失败时，修复问题后再继续。**不要跳过。**

### 4. 推送分支

```bash
# 再次确认不是 main
git branch --show-current

# 推送
git push -u origin HEAD
```

### 5. 创建 PR

```bash
# 写描述到临时文件
cat > /tmp/pr_body.md << 'EOF'
## 变更说明
<简要描述本次 PR 做了什么>

## 变更类型
- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 重构 (refactor)
- [ ] 文档 (docs)
- [ ] 测试 (test)

## 检查清单
- [ ] 代码已通过 lint 检查
- [ ] 测试已通过
- [ ] 数据库迁移已生成（如有模型变更）
- [ ] 无硬编码密钥/密码

## 相关 Issue
Fixes #
EOF

# 创建 PR
gh pr create --title "type(scope): 简要描述" --body-file /tmp/pr_body.md

# 清理
rm /tmp/pr_body.md
```

## 安全护栏

| 规则 | 说明 |
|------|------|
| **禁止 push main** | 最高优先级，每次 push 前必须确认分支 |
| **禁止跳过 preflight** | lint 和测试必须通过 |
| **禁止硬编码密钥** | 提交前检查 |
| **必须使用模板** | PR 描述必须包含检查清单 |

## PR 标题规范

```
type(scope): 中文简要描述
```

示例：
- `feat(devices): 添加电表批量导入功能`
- `fix(collector): 修复任务超时重试逻辑`
- `refactor(auth): 重构 JWT token 刷新机制`
