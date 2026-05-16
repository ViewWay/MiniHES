---
name: webapp-testing
description: |
  MiniHES 前后端测试。当用户需要编写测试、运行测试、调试测试失败、
  或提到 pytest、vitest、playwright 时激活。
  涵盖后端单元测试、前端组件测试、E2E 测试。
---

# MiniHES Web App Testing

## 何时使用

- 编写或运行后端测试 (pytest)
- 编写或运行前端测试 (vitest)
- 编写或运行 E2E 测试 (playwright)
- 调试测试失败
- 检查测试覆盖率

## 决策树

```
需要测试什么？
├── 后端 API / Service / Model
│   ├── 单函数逻辑 → pytest 单元测试
│   ├── API 端到端 → pytest + httpx AsyncClient
│   └── 数据库操作 → pytest + 真实数据库 / SQLite 内存
│
├── 前端组件 / 页面
│   ├── 组件逻辑 → vitest + Vue Test Utils
│   └── 样式快照 → vitest
│
└── 前后端集成
    └── 用户流程 → Playwright E2E
```

## 后端测试 (pytest)

### 目录结构

```
backend/tests/
├── backend/
│   ├── conftest.py       # fixtures
│   ├── factories.py      # 测试数据工厂
│   ├── unit/             # 单元测试（无外部依赖）
│   │   ├── test_services/
│   │   └── test_utils/
│   └── api/              # API 集成测试
│       ├── test_auth.py
│       ├── test_meters.py
│       └── test_tasks.py
```

### Fixtures

```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def auth_client(client):
    # 登录获取 token
    response = await client.post("/api/v1/auth/login", json={...})
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
```

### 编写规范

```python
import pytest

@pytest.mark.asyncio
async def test_create_meter(client, auth_client):
    """测试创建电表"""
    # Arrange
    data = {"serial_number": "TEST001", "meter_name": "测试电表"}

    # Act
    response = await auth_client.post("/api/v1/meters", json=data)

    # Assert
    assert response.status_code == 201
    assert response.json()["serial_number"] == "TEST001"
```

### 运行

```bash
cd backend

# 全部
uv run pytest

# 指定文件
uv run pytest tests/backend/api/test_meters.py

# 带覆盖率
uv run pytest --cov=app --cov-report=term-missing

# 只运行失败的
uv run pytest --lf

# 详细输出
uv run pytest -v
```

## 前端测试 (vitest)

### 目录结构

```
apps/web-antd/src/
├── views/
│   └── devices/
│       ├── MeterList.vue
│       └── __tests__/
│           └── MeterList.test.ts
├── components/
│   └── __tests__/
└── api/
    └── __tests__/
```

### 编写规范

```typescript
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import MeterStatusTag from '../MeterStatusTag.vue';

describe('MeterStatusTag', () => {
  it('renders online status', () => {
    const wrapper = mount(MeterStatusTag, {
      props: { status: 'online' },
    });
    expect(wrapper.text()).toContain('在线');
  });
});
```

### 运行

```bash
cd frontend

# 全部
pnpm run test

# 监听模式
pnpm run test:watch

# 覆盖率
pnpm run test:coverage

# UI 模式
pnpm run test:ui
```

## E2E 测试 (Playwright)

### 目录结构

```
tests/e2e/
├── playwright.config.ts
├── fixtures/
│   └── auth.ts
└── specs/
    ├── login.spec.ts
    ├── meter-management.spec.ts
    └── task-scheduling.spec.ts
```

### 编写规范

```typescript
import { test, expect } from '@playwright/test';

test('创建新电表', async ({ page }) => {
  // 登录
  await page.goto('http://localhost:5666/login');
  await page.fill('[placeholder="用户名"]', 'admin');
  await page.fill('[placeholder="密码"]', 'password');
  await page.click('button[type="submit"]');

  // 导航到设备管理
  await page.click('text=设备管理');
  await page.click('text=电表列表');

  // 创建电表
  await page.click('text=新增');
  await page.fill('[label="序列号"]', 'E2E-TEST-001');
  await page.fill('[label="电表名称"]', 'E2E测试电表');
  await page.click('text=确定');

  // 验证
  await expect(page.locator('text=E2E-TEST-001')).toBeVisible();
});
```

### 运行

```bash
# 全部浏览器
cd frontend && pnpm run test:e2e

# UI 模式
pnpm run test:e2e-ui

# 指定文件
npx playwright test specs/meter-management.spec.ts

# 调试模式
npx playwright test --debug
```

## 测试原则

### 通用

- **Arrange-Act-Assert** 模式
- 每个测试只验证一个行为
- 测试描述清晰（"应该..."）
- 不依赖执行顺序
- 测试数据独立，不共享状态

### 后端

- Service 层优先单元测试
- API 测试覆盖主要成功路径和错误路径
- 数据库测试用真实数据库（测试隔离）
- 不 mock ORM 方法，可以 mock 外部服务

### 前端

- 组件测试关注用户行为，不测内部实现
- Mock API 调用，不依赖后端
- 测试交互：点击、输入、提交
- 不测 CSS 样式细节

### E2E

- 覆盖关键用户流程
- 使用 data-testid 定位元素
- 每个测试独立（登录/数据准备）
- 不依赖其他测试的结果

## 覆盖率目标

| 层 | 目标 |
|---|------|
| 后端 Service | 80%+ |
| 后端 API | 70%+ |
| 前端组件 | 60%+ |
| E2E | 关键流程 100% |
