---
name: code-review
description: |
  MiniHES 代码审查。当用户请求审查代码、review PR、检查变更时激活。
  支持本地变更审查和指定文件审查，输出结构化审查报告。
  引用 backend-checklist.md 和 frontend-checklist.md 作为审查依据。
---

# MiniHES 代码审查

## 何时使用

- 用户说 "review"、"审查"、"检查代码"
- 提交 PR 前的代码审查
- 审查指定文件或目录
- 审查 git diff 中的变更

## 审查模式

### 模式 A：本地变更审查

```bash
# 查看变更范围
git status
git diff                      # 未暂存
git diff --staged             # 已暂存
```

审查所有待提交变更。

### 模式 B：指定文件审查

用户指定文件路径，逐文件按清单审查。

### 模式 C：PR 审查

```bash
# 获取 PR 变更
git diff main...HEAD --stat
git diff main...HEAD
```

## 审查维度

按以下六大支柱分析代码：

### 1. 正确性
- 逻辑是否正确，是否实现预期功能
- 边界条件是否处理
- 异步操作是否正确 await
- 数据库事务是否合理

### 2. 安全性
- 输入是否验证
- SQL 注入风险
- XSS / CSRF 防护
- 敏感信息是否泄露
- 权限检查是否存在

### 3. 性能
- N+1 查询问题
- 不必要的全表扫描
- 内存泄漏风险
- 大量数据的分页处理

### 4. 可维护性
- 代码是否清晰易懂
- 命名是否准确
- 函数是否过长（< 50 行）
- 是否有重复代码可提取

### 5. 架构合规
- 是否遵循分层架构（endpoints → schemas → services → models）
- 是否跨层调用
- 是否符合项目命名规范
- 是否符合表前缀约定

### 6. 测试覆盖
- 关键逻辑是否有测试
- 边界条件是否覆盖
- 错误路径是否测试

## 审查清单

- 后端代码：参见 [backend-checklist.md](references/backend-checklist.md)
- 前端代码：参见 [frontend-checklist.md](references/frontend-checklist.md)

## 输出模板

### Template A：有发现

```markdown
# Code Review

Found N urgent issues:

## 1 <brief description>
FilePath: <path> line <line>
<code snippet>

### Suggested fix
<fix description>

---

Found M suggestions for improvement:

## 1 <brief description>
FilePath: <path> line <line>
<code snippet>

### Suggested fix
<fix description>

---
```

问题超过 10 条时，输出前 10 条并注明 "10+ issues"。

如果存在需要修改代码的问题，末尾询问：**"是否需要我应用这些修复建议？"**

### Template B：无问题

```markdown
# Code Review
No issues found.
```

## 审查决策树

每次审查前，按此决策树判断审查重点：

```
代码变更 → 是否涉及数据库？
├─ 是 → 检查迁移、ForeignKey、索引、N+1
│
├─ 否 → 是否涉及 API 端点？
│   ├─ 是 → 检查 schema 验证、状态码、权限
│   │
│   └─ 否 → 是否涉及前端组件？
│       ├─ 是 → 检查类型安全、状态管理、交互反馈
│       │
│       └─ 否 → 通用审查（命名、结构、安全）
```

## 常见问题 → 修复方案

| 错误模式 | 检测方式 | 修复方案 |
|---------|---------|---------|
| `Mapped[dict]` 无 JSON 类型 | ruff 检查 model 文件 | 添加 `mapped_column(JSON, ...)` |
| async 函数内用 `time.sleep` | grep `time.sleep` | 替换为 `asyncio.sleep` |
| 未注册的新模型 | 检查 `models/__init__.py` | 添加导入和 `__all__` |
| NOT NULL 列无默认值且有数据 | alembic migrate 报错 | 先加 nullable 列 → 填充数据 → 改 NOT NULL |
| 前端直接用 axios | grep `axios` 或 `fetch` | 统一使用 `requestClient` |
| 组件内硬编码 API 地址 | grep `http://` / `https://` | 使用环境变量 |
| 缺少 loading 状态 | 检查异步操作 | 添加 `loading ref` + `a-spin` |
| 缺少删除确认 | 检查删除按钮 | 添加 `Modal.confirm()` |

## 审查流程

1. **识别变更范围**：确定审查哪些文件
2. **分类**：区分后端 (.py) 和前端 (.vue/.ts) 文件
3. **逐文件审查**：按对应清单检查
4. **汇总**：按严重程度（Critical → Suggestion）排列
5. **输出**：使用 Template A 或 B

## 审查语气

- 建设性、专业、简洁
- 说明**为什么**需要修改
- 认可好的代码实践
