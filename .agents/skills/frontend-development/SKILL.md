---
name: frontend-development
description: |
  MiniHES 前端开发规范。当用户进行 Vue 3 前端开发、组件设计、
  页面布局、样式调整时自动激活。
  涵盖技术栈、组件设计原则、设计规范、Ant Design Vue 用法。
---

# MiniHES 前端开发规范

## 何时使用

- 编写 Vue 3 组件、页面、路由
- 使用 Ant Design Vue 组件
- 调整样式、布局、交互
- 前端状态管理
- API 请求封装

## 技术栈

- **框架**: Vue 3 + TypeScript
- **UI 库**: Ant Design Vue
- **构建**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP**: 基于 @vben/request 封装
- **脚手架**: vue-vben-admin 5.7.0

## 目录结构

```
apps/web-antd/src/
├── api/              # API 请求封装
├── views/            # 页面组件（按业务模块）
│   ├── devices/     # 设备管理
│   ├── collector/   # 数据采集
│   ├── analysis/    # 分析报表
│   └── system/      # 系统管理
├── components/       # 全局共享组件
├── stores/           # Pinia stores
├── router/           # 路由配置
├── locales/          # 国际化
└── utils/            # 工具函数
```

## 组件设计原则

### 命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 页面 | PascalCase | `MeterList.vue`, `TaskDetail.vue` |
| 组件 | PascalCase + 业务前缀 | `MeterStatusTag.vue` |
| Composable | use + 功能 | `useMeterList.ts` |
| Store | use + 模块 + Store | `useMeterStore.ts` |
| API 文件 | 模块名小写 | `meter.ts`, `task.ts` |

### 组件结构顺序

```vue
<script setup lang="ts">
// 1. 导入
// 2. 类型定义
// 3. Props & Emits
// 4. Composables
// 5. 响应式数据
// 6. 计算属性
// 7. 方法
// 8. 生命周期
</script>

<template>
  <!-- 模板 -->
</template>

<style scoped lang="less">
/* 样式 */
</style>
```

### 组件设计规则

- 单一职责：一个组件做一件事
- Props 向下，Events 向上
- 复杂逻辑提取为 composable
- 列表渲染必须用 `:key`
- 条件渲染用 `v-show`（频繁切换）或 `v-if`（条件分支）

## API 封装

```typescript
// api/meter.ts
import { requestClient } from '#/api/request';

export async function getMeterList(params: MeterListParams) {
  return requestClient.get<MeterListResponse>('/api/v1/meters', { params });
}

export async function createMeter(data: CreateMeterRequest) {
  return requestClient.post<MeterDetail>('/api/v1/meters', data);
}
```

### 规则

- 每个 API 文件对应一个后端模块
- 使用 TypeScript 接口定义请求/响应类型
- 统一使用 `requestClient`，不直接用 axios
- 错误处理在 `requestClient` 层统一处理

## 状态管理

### 何时用 Store

| 场景 | 方案 |
|------|------|
| 组件内状态 | `ref` / `reactive` |
| 跨组件共享 | Pinia Store |
| 服务端数据 | API 直接请求 + 组件内缓存 |
| 全局配置 | Store |

### Store 结构

```typescript
// stores/meter.ts
import { defineStore } from 'pinia';

export const useMeterStore = defineStore('meter', () => {
  const meters = ref<Meter[]>([]);
  const loading = ref(false);

  async function fetchMeters(params?: MeterListParams) {
    loading.value = true;
    try {
      const res = await getMeterList(params);
      meters.value = res.items;
    } finally {
      loading.value = false;
    }
  }

  return { meters, loading, fetchMeters };
});
```

## 设计思维

开始编码前，先明确四个维度：

1. **Purpose**: 这个页面/组件解决什么问题？谁使用？
2. **Tone**: 选择一个明确的设计调性（工业感/数据仪表盘风/极简/专业严肃），全局保持一致
3. **Constraints**: 技术约束（框架、性能、无障碍）
4. **Differentiation**: 这个界面有什么让人记住的？一个清晰的数据可视化？一个流畅的交互？

**核心原则**: 选择一个明确的设计方向并精确执行。大胆极繁和精致极简都可行——关键是**有意图性**。

## 设计规范

参见 [design-checklist.md](references/design-checklist.md)。

### 排版与字体

- 选择有辨识度的字体组合，不要用 Inter/Roboto/Arial 等通用字体
- 数据面板用等宽字体（如 JetBrains Mono、Fira Code）
- 标题用有特色的 display font，正文用清晰的 UI font
- 字重对比：标题 600-700，正文 400，辅助文字 300

### 色彩与主题

- 主色跟随 Ant Design Vue 主题 token，不硬编码色值
- 使用 CSS 变量保持一致性
- 用深浅对比创造层次感，而不是均匀分布色彩
- 状态色统一：成功绿、失败红、进行中蓝、警告橙
- 禁止淡紫色渐变+白色背景这种 AI 通用配色

### 动效与微交互

- 页面加载使用错开显示（staggered reveal with animation-delay）
- 列表项、卡片入场动画增加层次感
- 悬停状态要有反馈（阴影变化、色彩加深、微位移）
- 数据刷新使用过渡动画
- 优先使用 CSS-only 方案，复杂交互用 Vue transition

### 空间构图

- 不总是使用对称网格，关键数据可以突出展示
- 利用重叠、留白、对角线引导视线
- 数据面板和仪表盘允许控制性密度
- 重要操作区域有足够的呼吸空间

### 背景与视觉细节

- 不使用纯色背景，加入细微纹理（噪点、网格线、渐变）
- 卡片用微妙阴影和边框增加深度
- 数据区域可以用几何图案或渐变网格
- 状态指示器使用发光效果或渐变填充

### 交互规范

- 加载状态：使用 `a-spin` 或骨架屏
- 空状态：使用 `a-empty`
- 错误提示：使用 `message.error()`
- 成功提示：使用 `message.success()`
- 删除操作：必须二次确认 `Modal.confirm()`

### 表单

- 使用 Ant Design Form 组件
- 必填字段标注 `*`
- 实时验证 (`validateTrigger: 'change'`)
- 提交时全量验证
- 提交按钮 loading 状态防止重复

## 输出格式

构建前端功能时，按以下格式输出：

1. **文件结构** — 展示文件应放在哪里
2. **完整代码** — 功能完整、有类型注解的代码
3. **依赖** — 需要安装的包
4. **环境变量** — 如有需要
5. **运行说明** — 如何启动和验证

## 性能优化

- 路由懒加载 (`() => import(...)`)
- 大列表用虚拟滚动
- 图片懒加载
- 避免不必要的响应式 (`shallowRef` / `markRaw`)
- 组件 `v-memo` 减少重渲染

## 禁止

- 直接操作 DOM（除非必要）
- 在模板中写复杂表达式
- 全局污染样式（必须 `scoped`）
- 硬编码 API 地址（使用环境变量）
- 提交 `console.log` 调试代码
