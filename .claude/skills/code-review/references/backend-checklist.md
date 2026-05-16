# 后端代码审查清单

## 架构合规

- [ ] endpoint 只处理 HTTP 逻辑，不含业务代码
- [ ] service 层处理业务逻辑，不直接操作 request/response
- [ ] schema 定义了请求/响应类型
- [ ] 数据库操作通过 ORM，无原生 SQL 拼接
- [ ] 新模型在 `__init__.py` 注册

## 数据库

- [ ] 新表有正确的模块前缀 (sys_/dev_/col_/lab_)
- [ ] ForeignKey 声明正确，有 ondelete 约束
- [ ] 查询有合理的索引支持
- [ ] 无 N+1 查询（使用 `selectinload` / `joinedload`）
- [ ] 批量操作使用批量插入而非循环单条
- [ ] 大量数据查询有分页限制

## 安全

- [ ] 用户输入通过 Pydantic schema 验证
- [ ] 无 SQL 字符串拼接
- [ ] 需要认证的接口有依赖注入检查
- [ ] 敏感操作有权限校验
- [ ] 密码/密钥不硬编码、不输出到日志
- [ ] 错误响应不暴露堆栈信息

## API 设计

- [ ] 使用正确的 HTTP 方法 (GET/POST/PUT/PATCH/DELETE)
- [ ] 使用正确的 HTTP 状态码
- [ ] 响应格式符合项目规范
- [ ] API 路径使用 kebab-case 复数形式
- [ ] 分页接口有 `page`、`page_size`、`total` 字段

## 异步

- [ ] async 函数正确使用 await
- [ ] 数据库操作使用 async session
- [ ] 无阻塞调用在 async 上下文中（如 time.sleep → asyncio.sleep）
- [ ] 并发操作使用 asyncio.gather

## 错误处理

- [ ] 可预期的错误有明确的异常处理
- [ ] 异常有合理的错误码和描述
- [ ] 数据库事务失败时正确 rollback
- [ ] 外部调用（网络、Redis）有超时和重试

## 代码质量

- [ ] 函数长度 < 50 行
- [ ] 无重复代码
- [ ] 变量命名准确
- [ ] 无未使用的导入
- [ ] 类型注解完整
