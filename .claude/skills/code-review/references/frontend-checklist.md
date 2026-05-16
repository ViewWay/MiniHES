# 前端代码审查清单

## 组件设计

- [ ] 组件职责单一
- [ ] Props 有 TypeScript 类型定义
- [ ] Events 使用 emit，不直接修改 props
- [ ] 复杂逻辑提取为 composable
- [ ] 列表渲染使用 `:key`
- [ ] 无直接 DOM 操作

## 类型安全

- [ ] API 响应有类型定义
- [ ] Props 有类型定义和默认值
- [ ] ref/reactive 有泛型类型
- [ ] 无 any 类型（除非必要且注释说明）
- [ ] 事件回调有类型

## 状态管理

- [ ] 组件内状态用 ref/reactive
- [ ] 跨组件共享用 Pinia Store
- [ ] Store 内异步操作有 loading 状态
- [ ] Store 无冗余状态（可从其他状态派生）

## 性能

- [ ] 路由使用懒加载
- [ ] 大列表考虑虚拟滚动
- [ ] 避免不必要的重渲染（computed vs watch）
- [ ] 图片有懒加载
- [ ] 无内存泄漏（定时器、事件监听器在 unmount 时清理）

## 样式

- [ ] 使用 scoped 样式
- [ ] 无全局样式污染
- [ ] 使用 Ant Design Token/变量，非硬编码颜色
- [ ] 响应式适配（至少 1280px+）

## API 调用

- [ ] 使用 requestClient 封装
- [ ] 请求/响应有 TypeScript 类型
- [ ] 加载状态有 spin/skeleton 提示
- [ ] 错误有 message.error 提示
- [ ] 提交按钮有 loading 防重复

## 安全

- [ ] 不在前端存储敏感信息（token 除外）
- [ ] 用户输入做 XSS 防护
- [ ] 不拼接 URL 参数（使用 params）
- [ ] API 地址使用环境变量

## 代码质量

- [ ] 无 console.log 调试代码
- [ ] 无注释掉的代码块
- [ ] 无未使用的导入和变量
- [ ] 模板中无复杂表达式
