---
name: update-docs
description: |
  文档更新。当用户说 "更新文档"、"文档需要同步"、"添加文档" 时激活。
  支持代码变更驱动的文档更新、新文档脚手架、文档审查。
---

# MiniHES 文档更新

## 何时使用

- 代码变更后需要更新文档
- 新功能需要编写文档
- 审查文档完整性
- 用户说 "更新文档"、"文档同步"、"写文档"

## 文档目录

```
docs/
├── planning/              # 项目规划
│   ├── development-plan.md        # 开发排期计划
│   ├── project-workflow.md        # 项目开发流程
│   └── phase-overview.md          # 阶段概览
├── tasks/                 # 需求文档
│   └── prd-cloud-metering-system.md
├── design/                # 设计文档
│   └── tech-review-and-architecture.md
├── api/                   # API 文档（按模块）
├── guides/                # 开发指南
│   └── testing-strategy.md
└── reports/               # 审查报告、复盘
```

**规则**：禁止在 docs/ 根目录直接放文件，必须进子目录。

## 工作流

### 模式 A：代码变更 → 文档更新

#### Step 1：识别变更

```bash
# 查看分支变更
git diff main...HEAD --stat
```

#### Step 2：映射到文档

| 变更位置 | 可能影响的文档 |
|---------|--------------|
| `app/models/` | 架构文档（数据模型部分） |
| `app/api/v1/endpoints/` | API 文档、PRD（功能描述） |
| `app/core/config.py` | 部署文档、环境配置 |
| `app/services/` | 架构文档（业务逻辑部分） |
| `app/adapters/` | 通信适配文档 |
| `app/dlms/` | 协议栈文档 |
| 前端页面/路由 | PRD（功能描述） |

#### Step 3：逐项更新

对每个需要更新的文档：
1. 读取当前内容
2. 展示计划修改的内容
3. 等待确认
4. 应用修改

#### Step 4：验证

- 检查文档中的代码示例是否仍正确
- 检查表格数据是否与代码一致
- 检查链接是否有效

### 模式 B：创建新文档

#### 文档类型

| 类型 | 模板 |
|------|------|
| 技术方案 | 标题 + 背景 + 方案 + 对比 + 决策 |
| API 文档 | 端点 + 参数 + 响应 + 示例 |
| 操作手册 | 前置条件 + 步骤 + 验证 + 常见问题 |
| 变更记录 | 日期 + 版本 + 变更内容 + 影响 |

#### 文档规范

- 使用中文编写
- Markdown 格式
- 代码块标注语言类型
- 表格用于对比和参数说明
- 标题层级不超过 4 级

### 模式 C：文档审查

检查项：
- [ ] 内容与当前代码一致
- [ ] 代码示例可运行
- [ ] API 路径和参数正确
- [ ] 架构图与实际一致
- [ ] 无过时的信息
- [ ] 链接有效

## 报告和文档约定

- 所有文档放在 `docs/` 目录
- 文件名使用 kebab-case：`tech-review-and-architecture.md`
- 日期格式：`YYYY-MM-DD`
- 版本号：语义化版本 `MAJOR.MINOR.PATCH`
