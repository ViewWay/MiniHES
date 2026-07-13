---
name: "source-command-review"
description: "代码审查工作流"
---

# source-command-review

Use this skill when the user asks to run the migrated source command `review`.

## Command Template

对当前更改进行全面审查。

## 审查项目

- **安全性** - 使用 security-reviewer agent
- **代码质量** - 使用 code-reviewer agent
- **类型检查** - TypeScript/Python 类型
- **测试覆盖** - 确保覆盖率 >= 80%

## 使用方法

```
/review
/review security
```
