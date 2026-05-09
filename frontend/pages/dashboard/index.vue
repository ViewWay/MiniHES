<template>
  <div class="dashboard-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo-mini" v-if="sidebarCollapsed">M</div>
        <div class="logo-full" v-else>
          <span class="logo-icon">⚡</span>
          <span class="logo-text">MINIHES</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div v-for="section in menuSections" :key="section.title" class="nav-section">
          <div class="nav-section-title" v-if="!sidebarCollapsed">{{ section.title }}</div>
          <NuxtLink
            v-for="item in section.items"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ 'active': currentPath === item.path }"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-text" v-if="!sidebarCollapsed">{{ item.label }}</span>
            <span class="nav-badge" v-if="item.badge && !sidebarCollapsed">{{ item.badge }}</span>
          </NuxtLink>
        </div>
      </nav>

      <div class="sidebar-footer">
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <button class="icon-btn" title="刷新数据" @click="refreshData">
            <span :class="{ 'spinning': isRefreshing }">🔄</span>
          </button>
          <button class="icon-btn" title="通知">
            <span>🔔</span>
            <span class="badge">3</span>
          </button>
          <div class="user-menu">
            <button class="user-btn" @click="showUserMenu = !showUserMenu">
              <div class="user-avatar">A</div>
              <span class="user-name">Admin</span>
              <span class="dropdown-icon">▼</span>
            </button>
            <Transition name="dropdown">
              <div v-if="showUserMenu" class="user-dropdown">
                <div class="dropdown-item">👤 个人设置</div>
                <div class="dropdown-item">🔐 修改密码</div>
                <hr class="dropdown-divider">
                <div class="dropdown-item danger" @click="handleLogout">🚪 退出登录</div>
              </div>
            </Transition>
          </div>
        </div>
      </header>

      <!-- 仪表盘内容 -->
      <main class="dashboard-main">
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div
            v-for="stat in stats"
            :key="stat.key"
            class="stat-card"
            :class="stat.variant"
          >
            <div class="stat-header">
              <span class="stat-icon">{{ stat.icon }}</span>
              <span class="stat-trend" :class="stat.trendClass">
                {{ stat.trend }}
              </span>
            </div>
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-chart">
              <svg viewBox="0 0 100 20" class="mini-chart">
                <path
                  :d="stat.chartPath"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- 主图表区域 -->
        <div class="charts-row">
          <!-- 实时用电曲线 -->
          <div class="chart-card large">
            <div class="chart-header">
              <div>
                <h3 class="chart-title">实时用电功率</h3>
                <p class="chart-subtitle">Real-time Power Consumption</p>
              </div>
              <div class="chart-actions">
                <button
                  v-for="period in timePeriods"
                  :key="period.value"
                  class="period-btn"
                  :class="{ 'active': selectedPeriod === period.value }"
                  @click="selectedPeriod = period.value"
                >
                  {{ period.label }}
                </button>
              </div>
            </div>
            <div class="chart-body">
              <div class="chart-legend">
                <span class="legend-item">
                  <span class="legend-dot primary"></span>
                  有功功率 (kW)
                </span>
                <span class="legend-item">
                  <span class="legend-dot secondary"></span>
                  无功功率 (kvar)
                </span>
              </div>
              <div class="chart-placeholder">
                <svg viewBox="0 0 800 300" class="main-chart">
                  <g class="grid-lines" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4">
                    <line v-for="i in 5" :key="i" :y1="i * 50" :y2="i * 50" x1="60" x2="760"/>
                    <line v-for="i in 8" :key="`v${i}`" :x1="60 + i * 87.5" :x2="60 + i * 87.5" y1="20" y2="270"/>
                  </g>
                  <g class="y-labels" fill="#94A3B8" font-size="11" text-anchor="end">
                    <text v-for="(label, i) in ['500', '400', '300', '200', '100', '0']" :key="label" x="50" :y="25 + i * 50">{{ label }}</text>
                  </g>
                  <path
                    class="data-line primary-line"
                    :d="activePowerPath"
                    fill="none"
                    stroke="#10B981"
                    stroke-width="2.5"
                  />
                  <path
                    class="data-line secondary-line"
                    :d="reactivePowerPath"
                    fill="none"
                    stroke="#3B82F6"
                    stroke-width="2"
                  />
                  <defs>
                    <linearGradient id="primaryGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stop-color="#10B981" stop-opacity="0.3"/>
                      <stop offset="100%" stop-color="#10B981" stop-opacity="0"/>
                    </linearGradient>
                  </defs>
                  <path :d="activePowerArea" fill="url(#primaryGradient)"/>
                </svg>
              </div>
            </div>
          </div>

          <!-- 设备状态 -->
          <div class="chart-card">
            <div class="chart-header">
              <div>
                <h3 class="chart-title">设备状态</h3>
                <p class="chart-subtitle">Device Status</p>
              </div>
            </div>
            <div class="chart-body">
              <div class="device-status-list">
                <div v-for="device in deviceStatus" :key="device.name" class="device-item">
                  <div class="device-info">
                    <span class="device-icon">{{ device.icon }}</span>
                    <span class="device-name">{{ device.name }}</span>
                  </div>
                  <span class="device-status" :class="device.statusClass">
                    {{ device.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-card">
          <div class="table-header">
            <div>
              <h3 class="table-title">最近抄表记录</h3>
              <p class="table-subtitle">Recent Meter Readings</p>
            </div>
            <button class="export-btn">📥 导出数据</button>
          </div>
          <div class="table-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>设备编号</th>
                  <th>设备名称</th>
                  <th>抄表时间</th>
                  <th>有功电能</th>
                  <th>无功电能</th>
                  <th>功率因数</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in readings" :key="record.id">
                  <td class="mono">{{ record.deviceId }}</td>
                  <td>{{ record.deviceName }}</td>
                  <td>{{ record.timestamp }}</td>
                  <td class="value">{{ record.activeEnergy }} kWh</td>
                  <td class="value">{{ record.reactiveEnergy }} kvarh</td>
                  <td class="value">{{ record.powerFactor }}</td>
                  <td><span class="status-badge" :class="record.statusClass">{{ record.status }}</span></td>
                  <td><button class="action-btn">详情</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'default',
  auth: true
})

const sidebarCollapsed = ref(false)
const showUserMenu = ref(false)
const isRefreshing = ref(false)
const selectedPeriod = ref('1h')

const route = useRoute()
const currentPath = computed(() => route.path)

const pageTitle = computed(() => {
  const path = route.path
  if (path === '/dashboard') return '仪表盘'
  if (path.includes('devices')) return '设备管理'
  if (path.includes('monitor')) return '实时监控'
  if (path.includes('analysis')) return '数据分析'
  return '仪表盘'
})

const menuSections = [
  {
    title: '主要功能',
    items: [
      { path: '/dashboard', icon: '📊', label: '仪表盘' },
      { path: '/dashboard/devices', icon: '🔌', label: '设备管理', badge: '128' },
      { path: '/dashboard/monitor', icon: '📈', label: '实时监控' },
      { path: '/dashboard/analysis', icon: '📉', label: '数据分析' },
    ]
  },
  {
    title: '系统管理',
    items: [
      { path: '/dashboard/tasks', icon: '⏰', label: '采集任务' },
      { path: '/dashboard/alerts', icon: '🚨', label: '告警管理', badge: '3' },
      { path: '/dashboard/settings', icon: '⚙️', label: '系统设置' },
    ]
  }
]

const stats = ref([
  {
    key: 'totalDevices',
    icon: '🔌',
    value: '128',
    label: '在线设备',
    trend: '+12',
    trendClass: 'up',
    variant: 'primary',
    chartPath: 'M0,15 Q10,10 20,12 T40,8 T60,10 T80,5 T100,10'
  },
  {
    key: 'totalPower',
    icon: '⚡',
    value: '2,847 kW',
    label: '实时功率',
    trend: '+5.3%',
    trendClass: 'up',
    variant: 'success',
    chartPath: 'M0,12 Q10,14 20,10 T40,8 T60,12 T80,6 T100,8'
  },
  {
    key: 'todayEnergy',
    icon: '📊',
    value: '45,238 kWh',
    label: '今日用电',
    trend: '-2.1%',
    trendClass: 'down',
    variant: 'warning',
    chartPath: 'M0,8 Q10,12 20,10 T40,14 T60,8 T80,10 T100,12'
  },
  {
    key: 'alerts',
    icon: '🚨',
    value: '3',
    label: '活跃告警',
    trend: '-5',
    trendClass: 'neutral',
    variant: 'danger',
    chartPath: 'M0,10 Q10,10 20,10 T40,10 T60,10 T80,10 T100,10'
  }
])

const timePeriods = [
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' },
  { label: '7天', value: '7d' }
]

const deviceStatus = ref([
  { name: '红外适配器', icon: '📡', status: '正常', statusClass: 'online' },
  { name: 'NB-IoT 网关', icon: '📶', status: '正常', statusClass: 'online' },
  { name: 'M-Bus 集中器', icon: '🔧', status: '维护中', statusClass: 'warning' },
  { name: 'LoRaWAN 网关', icon: '📡', status: '离线', statusClass: 'offline' },
  { name: 'PLC 调制解调器', icon: '⚡', status: '正常', statusClass: 'online' },
])

const readings = ref([
  {
    id: 1,
    deviceId: 'DLMS001',
    deviceName: '1号楼总表',
    timestamp: '2024-01-15 14:30:00',
    activeEnergy: '15,234.56',
    reactiveEnergy: '1,234.78',
    powerFactor: '0.95',
    status: '正常',
    statusClass: 'success'
  },
  {
    id: 2,
    deviceId: 'DLMS002',
    deviceName: '2号楼总表',
    timestamp: '2024-01-15 14:29:45',
    activeEnergy: '12,456.78',
    reactiveEnergy: '987.65',
    powerFactor: '0.92',
    status: '正常',
    statusClass: 'success'
  },
  {
    id: 3,
    deviceId: 'DLMS003',
    deviceName: '3号楼总表',
    timestamp: '2024-01-15 14:29:30',
    activeEnergy: '18,789.12',
    reactiveEnergy: '1,456.23',
    powerFactor: '0.88',
    status: '预警',
    statusClass: 'warning'
  },
  {
    id: 4,
    deviceId: 'DLMS004',
    deviceName: '商业区总表',
    timestamp: '2024-01-15 14:29:15',
    activeEnergy: '45,678.90',
    reactiveEnergy: '3,456.78',
    powerFactor: '0.97',
    status: '正常',
    statusClass: 'success'
  },
  {
    id: 5,
    deviceId: 'DLMS005',
    deviceName: '地下车库照明',
    timestamp: '2024-01-15 14:29:00',
    activeEnergy: '3,456.12',
    reactiveEnergy: '234.56',
    powerFactor: '0.85',
    status: '异常',
    statusClass: 'error'
  }
])

const activePowerPath = computed(() => {
  return 'M60,200 C120,180 180,220 240,150 S360,100 420,120 S540,80 600,100 S720,60 760,80'
})

const reactivePowerPath = computed(() => {
  return 'M60,230 C120,220 180,240 240,200 S360,180 420,190 S540,160 600,180 S720,140 760,160'
})

const activePowerArea = computed(() => {
  const line = 'M60,200 C120,180 180,220 240,150 S360,100 420,120 S540,80 600,100 S720,60 760,80'
  return `${line} L760,270 L60,270 Z`
})

const refreshData = async () => {
  isRefreshing.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))
  isRefreshing.value = false
}

const handleLogout = async () => {
  await navigateTo('/')
}
</script>

<style scoped>
:root {
  --color-primary: #10B981;
  --color-secondary: #3B82F6;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-bg: #0F172A;
  --color-bg-light: #1E293B;
  --color-bg-lighter: #334155;
  --color-text: #E2E8F0;
  --color-text-muted: #94A3B8;
  --color-border: #334155;
  --sidebar-width: 240px;
  --sidebar-collapsed: 64px;
  --header-height: 64px;
}

.dashboard-container {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: 'Noto Sans SC', sans-serif;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-bg-light);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: relative;
  z-index: 50;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed);
}

.sidebar-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-border);
}

.logo-full {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: var(--color-primary);
  letter-spacing: 2px;
}

.logo-mini {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: 8px;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 16px;
  color: white;
  margin: 0 auto;
}

.sidebar-nav {
  flex: 1;
  padding: 24px 0;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 24px;
}

.nav-section-title {
  padding: 0 24px;
  margin-bottom: 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--color-text-muted);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 24px;
  margin: 2px 8px;
  border-radius: 8px;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: all 0.3s ease;
  position: relative;
}

.nav-item:hover {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-text);
}

.nav-item.active {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-primary);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-text {
  flex: 1;
  font-size: 13px;
}

.nav-badge {
  background: var(--color-error);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--color-border);
}

.collapse-btn {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  height: var(--header-height);
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 18px;
}

.icon-btn:hover {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-primary);
}

.icon-btn .badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-error);
  color: white;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-btn:hover {
  border-color: var(--color-primary);
}

.user-avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  font-size: 13px;
}

.dropdown-icon {
  font-size: 10px;
  color: var(--color-text-muted);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.dropdown-item {
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dropdown-item:hover {
  background: rgba(16, 185, 129, 0.1);
}

.dropdown-item.danger {
  color: var(--color-error);
}

.dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.dropdown-divider {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 4px 0;
}

.dashboard-main {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--color-primary);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.stat-card.primary::before { background: var(--color-primary); }
.stat-card.success::before { background: var(--color-primary); }
.stat-card.warning::before { background: var(--color-warning); }
.stat-card.danger::before { background: var(--color-error); }

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-icon {
  font-size: 24px;
}

.stat-trend {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.stat-trend.up {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-primary);
}

.stat-trend.down {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-primary);
}

.stat-trend.neutral {
  background: rgba(148, 163, 184, 0.2);
  color: var(--color-text-muted);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.stat-chart {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  opacity: 0.3;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  overflow: hidden;
}

.chart-card.large {
  grid-column: 1 / -1;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--color-border);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 2px 0;
}

.chart-subtitle {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}

.chart-actions {
  display: flex;
  gap: 4px;
}

.period-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.period-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}

.period-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.chart-body {
  padding: 24px;
}

.chart-legend {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.primary { background: var(--color-primary); }
.legend-dot.secondary { background: var(--color-secondary); }

.chart-placeholder {
  position: relative;
}

.main-chart {
  width: 100%;
  height: auto;
}

.grid-lines line {
  opacity: 0.3;
}

.data-line {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.primary-line {
  animation: drawLine 2s ease forwards;
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
}

@keyframes drawLine {
  to { stroke-dashoffset: 0; }
}

.secondary-line {
  opacity: 0.7;
}

.device-status-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  font-size: 20px;
}

.device-name {
  font-size: 13px;
}

.device-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.device-status.online {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-primary);
}

.device-status.warning {
  background: rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
}

.device-status.offline {
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-error);
}

.table-card {
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--color-border);
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 2px 0;
}

.table-subtitle {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}

.export-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.export-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.table-body {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 24px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: rgba(51, 65, 85, 0.3);
  white-space: nowrap;
}

.data-table td {
  padding: 12px 24px;
  border-top: 1px solid var(--color-border);
  font-size: 13px;
}

.data-table tr:hover td {
  background: rgba(51, 65, 85, 0.3);
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.value {
  font-family: 'JetBrains Mono', monospace;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-primary);
}

.status-badge.warning {
  background: rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-error);
}

.action-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s ease;
  transform-origin: top right;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

@media (max-width: 1024px) {
  .charts-row {
    grid-template-columns: 1fr;
  }

  .chart-card.large {
    grid-column: 1;
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    height: 100%;
    transform: translateX(-100%);
  }

  .sidebar.collapsed {
    transform: translateX(0);
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .topbar {
    padding: 0 16px;
  }

  .dashboard-main {
    padding: 16px;
  }
}
</style>
