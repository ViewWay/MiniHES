# MiniHES 测试策略

**版本**: v1.0
**日期**: 2026-05-16

---

## 一、测试全景

```
┌─────────────────────────────────────────────────────────────────┐
│                        测试金字塔                                │
│                                                                 │
│                         ╱  E2E ╲          ← Playwright          │
│                       ╱  系统测试  ╲                              │
│                     ╱────────────────╲                           │
│                   ╱   API 集成测试    ╲    ← pytest + httpx       │
│                 ╱──────────────────────╲                         │
│               ╱   组件测试 / 服务测试    ╲  ← Vitest / pytest     │
│             ╱────────────────────────────╲                       │
│           ╱        单元测试 / 工具测试       ╲  ← Vitest / pytest │
│         ╱────────────────────────────────────╲                   │
│                                                                 │
│  前端: Vitest + Vue Test Utils + Playwright                    │
│  后端: pytest + pytest-asyncio + httpx                         │
│  CI: GitHub Actions (自动化)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、后端测试

### 2.1 测试分层

| 层级 | 工具 | 目标 | 目录 |
|------|------|------|------|
| 单元测试 | pytest | Service/工具函数逻辑 | `tests/backend/unit/` |
| API 集成测试 | pytest + httpx | 端点请求/响应 | `tests/backend/api/` |
| 数据库测试 | pytest + PostgreSQL | ORM + 迁移 | `tests/backend/db/` |
| 性能测试 | Locust | API 压力/并发 | `tests/backend/perf/` |

### 2.2 后端测试目录结构

```
tests/backend/
├── conftest.py              # 全局 fixtures
├── pytest.ini
├── factories.py             # 测试数据工厂 (faker)
├── unit/                    # 单元测试
│   ├── test_security.py     # JWT/密码哈希
│   ├── test_response.py     # 统一响应格式
│   └── test_scheduler.py    # 调度器逻辑
├── api/                     # API 集成测试
│   ├── test_auth.py         # 登录/登出/刷新
│   ├── test_meters.py       # 样机 CRUD + 状态流转
│   ├── test_projects.py     # 项目管理
│   ├── test_tasks.py        # 采集任务
│   ├── test_analysis.py     # 数据分析
│   ├── test_alarms.py       # 告警
│   ├── test_tests.py        # 测试管理
│   ├── test_system.py       # 用户/角色/部门
│   └── test_screens.py      # 大屏
├── db/                      # 数据库测试
│   ├── test_models.py       # ORM 模型
│   └── test_migrations.py   # 迁移一致性
└── perf/                    # 性能测试
    └── locustfile.py        # Locust 压测脚本
```

### 2.3 关键 Fixtures 设计

```python
# conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# 测试数据库（SQLite 内存或测试 PG）
TEST_DB_URL = "sqlite+aiosqlite:///test.db"
# 或用真实 PG: "postgresql+asyncpg://postgres:test@localhost:5432/metering_test"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL)
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_all_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_all_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine)
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    """带数据库的测试客户端，自动覆盖依赖"""
    from app.core.dependencies import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_client(client):
    """带认证的测试客户端"""
    # 先创建测试用户并获取 token
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "testadmin", "password": "Test123456!"
    })
    token = login_resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### 2.4 API 测试示例

```python
# api/test_meters.py
import pytest

@pytest.mark.asyncio
async def test_create_meter(auth_client):
    resp = await auth_client.post("/api/v1/meters", json={
        "serial_number": "DLMS2024001",
        "meter_name": "测试电表01",
        "meter_type_id": 1,
        "project_id": 1,
        "protocol": "DLMS",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 201
    assert data["data"]["serial_number"] == "DLMS2024001"
    assert data["data"]["current_status"] == "in_stock"

@pytest.mark.asyncio
async def test_meter_status_transition(auth_client):
    # 创建 → 挂表测试
    create = await auth_client.post("/api/v1/meters", json={...})
    meter_id = create.json()["data"]["id"]

    resp = await auth_client.post(f"/api/v1/meters/{meter_id}/status", json={
        "status": "testing",
        "reason": "开始挂表测试"
    })
    assert resp.status_code == 200

    # 验证非法状态转换
    resp = await auth_client.post(f"/api/v1/meters/{meter_id}/status", json={
        "status": "scrapped",
        "reason": "不合法的转换"
    })
    assert resp.status_code == 400
    assert resp.json()["code"] == 10002

@pytest.mark.asyncio
async def test_list_meters_pagination(auth_client):
    resp = await auth_client.get("/api/v1/meters?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
```

### 2.5 性能测试 (Locust)

```python
# perf/locustfile.py
from locust import HttpUser, task, between

class MiniHESUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "testuser", "password": "Test123456!"
        })
        self.token = resp.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_meters(self):
        self.client.get("/api/v1/meters?page=1&page_size=20", headers=self.headers)

    @task(2)
    def list_tasks(self):
        self.client.get("/api/v1/tasks?page=1&page_size=20", headers=self.headers)

    @task(1)
    def dashboard_overview(self):
        self.client.get("/api/v1/screens/overview", headers=self.headers)
```

---

## 三、前端测试

### 3.1 测试分层

| 层级 | 工具 | 目标 | 目录 |
|------|------|------|------|
| 单元测试 | Vitest | 工具函数/Store 逻辑 | `src/**/__tests__/` |
| 组件测试 | Vitest + Vue Test Utils | 组件渲染/交互 | `src/**/__tests__/` |
| E2E 测试 | Playwright | 用户流程 | `tests/e2e/` |
| 视觉回归 | Playwright 截图对比 | UI 外观 | `tests/e2e/visual/` |

### 3.2 前端测试目录结构

```
frontend/apps/web-antd/
├── vitest.config.ts                 # Vitest 配置
├── src/
│   ├── views/
│   │   ├── meter/
│   │   │   └── __tests__/
│   │   │       ├── list.test.ts     # 组件测试
│   │   │       └── detail.test.ts
│   │   └── task/
│   │       └── __tests__/
│   │           └── create.test.ts
│   └── utils/
│       └── __tests__/
│           └── format.test.ts       # 单元测试
│
tests/e2e/                           # E2E 测试（已存在）
├── playwright.config.ts
├── auth/
│   ├── common/auth.ts               # 登录辅助
│   └── login.spec.ts
├── meter/
│   ├── list.spec.ts                 # 样机列表流程
│   ├── create.spec.ts               # 样机入库流程
│   └── status-flow.spec.ts          # 状态流转
├── task/
│   ├── create.spec.ts               # 创建采集任务
│   └── monitor.spec.ts              # 任务监控
├── system/
│   ├── user.spec.ts                 # 用户管理
│   └── role.spec.ts                 # 角色管理
└── visual/                          # 视觉回归测试
    └── pages.spec.ts                # 截图对比
```

### 3.3 Vitest 配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    include: ['src/**/__tests__/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,vue}'],
      exclude: ['src/**/__tests__/**'],
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
});
```

### 3.4 组件测试示例

```typescript
// src/views/meter/__tests__/list.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import MeterList from '../list.vue';

// mock API
vi.mock('@/api/meter', () => ({
  getMeterList: vi.fn(() => Promise.resolve({
    code: 200,
    data: {
      items: [
        { id: 1, serial_number: 'DLMS001', current_status: 'in_stock' },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    },
  })),
}));

describe('MeterList', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders meter list', async () => {
    const wrapper = mount(MeterList, {
      global: { plugins: [createPinia()] },
    });
    // 等待异步数据加载
    await wrapper.vm.$nextTick();
    expect(wrapper.find('table').exists()).toBe(true);
  });
});
```

### 3.5 E2E 测试示例

```typescript
// tests/e2e/meter/create.spec.ts
import { test, expect } from '@playwright/test';
import { login } from '../auth/common/auth';

test.describe('样机入库', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('创建新样机', async ({ page }) => {
    await page.goto('/meter/list');
    await page.click('button:has-text("新增")');

    // 填写表单
    await page.fill('[data-testid="serial-number"]', 'DLMS2024001');
    await page.fill('[data-testid="meter-name"]', '测试电表01');
    await page.selectOption('[data-testid="meter-type"]', 'DCSP');
    await page.selectOption('[data-testid="project"]', 'Coral项目');
    await page.fill('[data-testid="manufacturer"]', '厂商A');

    await page.click('button:has-text("确定")');

    // 验证成功
    await expect(page.locator('.ant-message-success')).toBeVisible();
    await expect(page.locator('text=DLMS2024001')).toBeVisible();
  });

  test('序列号重复校验', async ({ page }) => {
    await page.goto('/meter/list');
    await page.click('button:has-text("新增")');

    await page.fill('[data-testid="serial-number"]', 'DLMS_EXISTING');
    await page.click('button:has-text("确定")');

    await expect(page.locator('text=序列号已存在')).toBeVisible();
  });
});
```

### 3.6 视觉回归测试

```typescript
// tests/e2e/visual/pages.spec.ts
import { test, expect } from '@playwright/test';
import { login } from '../auth/common/auth';

const pages = [
  { name: '仪表盘', path: '/dashboard' },
  { name: '样机列表', path: '/meter/list' },
  { name: '任务列表', path: '/task/list' },
  { name: '数据分析', path: '/analysis/daily' },
  { name: '系统用户', path: '/system/user' },
];

for (const { name, path } of pages) {
  test(`${name} 视觉回归`, async ({ page }) => {
    await login(page);
    await page.goto(path);
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot(`${name}.png`, {
      maxDiffPixelRatio: 0.01,
    });
  });
}
```

---

## 四、CI/CD 自动化

### 4.1 GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: metering_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd backend && uv sync
      - run: cd backend && uv run pytest --cov=app --cov-report=xml -v
      - uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: cd frontend && pnpm install
      - run: cd frontend/apps/web-antd && pnpm test -- --coverage
      - uses: codecov/codecov-action@v4

  e2e-test:
    runs-on: ubuntu-latest
    needs: [backend-test, frontend-test]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: metering_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - run: cd frontend && pnpm install
      - run: cd frontend && pnpm build:antd
      - run: cd frontend/apps/web-antd && pnpm preview &
      - run: cd tests/e2e && npm install && npx playwright install --with-deps
      - run: cd tests/e2e && npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: e2e-report
          path: tests/e2e/test-results/
```

---

## 五、测试覆盖率目标

| 层级 | 目标 | 说明 |
|------|------|------|
| 后端 API 测试 | > 90% | 所有端点全覆盖 |
| 后端 Service 单元测试 | > 80% | 核心业务逻辑 |
| 前端组件测试 | > 60% | 关键交互组件 |
| E2E 关键路径 | 100% | 登录、CRUD、状态流转、任务执行 |
| 性能基线 | P95 < 500ms | API 响应时间 |

---

## 六、现有测试待完善项

| 项目 | 状态 | 待做 |
|------|------|------|
| E2E Playwright | ✅ 框架搭建完成 | 补充 meter/task/system 测试用例 |
| 后端 pytest | ✅ 框架搭建完成 | 补充 conftest fixtures + 业务测试 |
| 前端 Vitest | ❌ 未搭建 | 配置 + 组件测试 |
| CI/CD | ❌ 未搭建 | GitHub Actions workflow |
| 视觉回归 | ❌ 未搭建 | Playwright 截图对比 |
| 性能测试 | ❌ 未搭建 | Locust 脚本 |

**建议推进顺序**：后端 pytest → 前端 Vitest → E2E 补充 → CI/CD → 性能测试 → 视觉回归
