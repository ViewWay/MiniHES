<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  Progress,
  Row,
  Spin,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  getAlarmList,
  getAlarmStats,
} from '#/api/modules/alarm';
import { getMeterList } from '#/api/modules/meter';
import { getProjectList } from '#/api/modules/project';
import { getTaskList } from '#/api/modules/task';
import { ALARM_SEVERITY_MAP, ALARM_TYPE_MAP } from '#/constants';
import { useChartTheme } from '#/composables/useChartTheme';

// --- Stats ---
const statsLoading = ref(false);
const onlineDevices = ref(0);
const totalDevices = ref(0);
const todayCollections = ref(0);
const activeAlarms = ref(0);
const runningTasks = ref(0);

// --- Projects ---
const projects = ref<any[]>([]);
const projectsLoading = ref(false);

const projectColumns = [
  { title: '项目名称', dataIndex: 'name', ellipsis: true },
  { title: '设备数', dataIndex: 'device_count', width: 80 },
  { title: '在线', dataIndex: 'online_count', width: 80 },
  { title: '进度', key: 'progress', width: 180 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
];

// --- Recent alarms ---
const recentAlarms = ref<any[]>([]);
const alarmsLoading = ref(false);

const alarmColumns = [
  { title: '设备', dataIndex: 'meter_name', width: 120, ellipsis: true },
  { title: '类型', dataIndex: 'alarm_type', key: 'alarm_type', width: 100 },
  { title: '级别', dataIndex: 'severity', key: 'severity', width: 70 },
  { title: '消息', dataIndex: 'alarm_message', ellipsis: true },
  { title: '时间', dataIndex: 'created_at', width: 160 },
];

const severityMap = Object.fromEntries(
  Object.entries(ALARM_SEVERITY_MAP).map(([key, val]) => [key, { color: val.color, text: val.label }]),
);

const typeMap = ALARM_TYPE_MAP;

// --- Chart ---
const trendChartRef = ref<EchartsUIType>();
const { renderEcharts: renderTrendChart } = useEcharts(trendChartRef);
const trendLoading = ref(false);
const { themedAxis, themedTooltip, watchThemeAndRerender } = useChartTheme();

// --- Fetch functions ---
async function fetchStats() {
  statsLoading.value = true;
  try {
    const [metersRes, alarmsRes, tasksRes] = await Promise.allSettled([
      getMeterList({ page: 1, page_size: 1 }),
      getAlarmStats(),
      getTaskList({ page: 1, page_size: 1 }),
    ]);

    if (metersRes.status === 'fulfilled') {
      totalDevices.value = metersRes.value?.total ?? 0;
      const items = metersRes.value?.items ?? [];
      onlineDevices.value =
        metersRes.value?.online_count
        ?? items.filter(
          (m: any) => m.status === 'online' || m.status === 'in_use',
        ).length
        ?? totalDevices.value;
    }

    if (alarmsRes.status === 'fulfilled') {
      const stats = alarmsRes.value;
      activeAlarms.value = stats?.unhandled_count ?? stats?.active ?? 0;
    }

    if (tasksRes.status === 'fulfilled') {
      const taskData = tasksRes.value;
      runningTasks.value = taskData?.running_count ?? 0;
      todayCollections.value = taskData?.today_executions ?? 0;
    }
  } catch {
    // Silent fallback: stats remain 0
  } finally {
    statsLoading.value = false;
  }
}

async function fetchProjects() {
  projectsLoading.value = true;
  try {
    const res = await getProjectList({ page: 1 });
    const items = res?.items ?? res ?? [];
    projects.value = items.map((p: any) => ({
      ...p,
      device_count: p.device_count ?? p.meter_count ?? 0,
      online_count: p.online_count ?? 0,
      progress:
        p.progress
        ?? (p.device_count
          ? Math.round((p.online_count / p.device_count) * 100)
          : 0),
    }));
  } catch {
    projects.value = [];
  } finally {
    projectsLoading.value = false;
  }
}

async function fetchRecentAlarms() {
  alarmsLoading.value = true;
  try {
    const res = await getAlarmList({ page: 1, page_size: 5 });
    recentAlarms.value = res?.items ?? res ?? [];
  } catch {
    recentAlarms.value = [];
  } finally {
    alarmsLoading.value = false;
  }
}

async function fetchTrendChart() {
  trendLoading.value = true;
  try {
    const res = await getAlarmList({ page: 1, page_size: 50 });
    const items = res?.items ?? res ?? [];

    const now = new Date();
    const days: string[] = [];
    const successRates: number[] = [];

    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const label = `${d.getMonth() + 1}/${d.getDate()}`;
      days.push(label);

      const dayStr = d.toISOString().slice(0, 10);
      const dayAlarms = items.filter((a: any) =>
        a.created_at?.startsWith(dayStr),
      );
      const handled = dayAlarms.filter(
        (a: any) => a.is_handled,
      ).length;
      const total = dayAlarms.length;
      successRates.push(
        total > 0 ? Math.round((handled / total) * 100) : 100,
      );
    }

    renderTrendChart({
      title: {
        text: '采集成功率趋势 (近7天)',
        left: 'center',
        textStyle: { fontSize: 14 },
      },
      tooltip: themedTooltip({
        formatter: (params: any) => {
          const p = params[0];
          return `${p.axisValue}<br/>成功率: <b>${p.value}%</b>`;
        },
      }),
      grid: {
        top: 50,
        left: '3%',
        right: '4%',
        bottom: 10,
        containLabel: true,
      },
      xAxis: themedAxis('x', { type: 'category', data: days, boundaryGap: false }),
      yAxis: themedAxis('y', { type: 'value', name: '成功率 (%)', min: 0, max: 100, splitNumber: 5, axisLabel: { formatter: '{value}%' } }),
      series: [
        {
          name: '成功率',
          type: 'line',
          data: successRates,
          smooth: true,
          areaStyle: {
            color: {
              colorStops: [
                { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
                { offset: 1, color: 'rgba(82, 196, 26, 0.05)' },
              ],
              x1: 0,
              x2: 0,
              y1: 0,
              y2: 1,
              type: 'linear',
            },
          },
          lineStyle: { color: '#52c41a', width: 2 },
          itemStyle: { color: '#52c41a' },
          markLine: {
            silent: true,
            data: [
              {
                yAxis: 95,
                lineStyle: { color: '#faad14', type: 'dashed' },
                label: { formatter: '目标 95%', position: 'insideEndTop' },
              },
            ],
          },
        },
      ],
    });
  } catch {
    const days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return `${d.getMonth() + 1}/${d.getDate()}`;
    });
    renderTrendChart({
      title: {
        text: '采集成功率趋势 (近7天)',
        left: 'center',
        textStyle: { fontSize: 14 },
      },
      tooltip: themedTooltip(),
      grid: {
        top: 50,
        left: '3%',
        right: '4%',
        bottom: 10,
        containLabel: true,
      },
      xAxis: themedAxis('x', { type: 'category', data: days }),
      yAxis: themedAxis('y', { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } }),
      series: [{ type: 'line', data: [0, 0, 0, 0, 0, 0, 0], smooth: true }],
    });
  } finally {
    trendLoading.value = false;
  }
}

async function loadAll() {
  await Promise.allSettled([
    fetchStats(),
    fetchProjects(),
    fetchRecentAlarms(),
    fetchTrendChart(),
  ]);
}

onMounted(() => {
  loadAll();
  watchThemeAndRerender(fetchTrendChart);
});
</script>

<template>
  <Page auto-content-height>
    <Spin :spinning="statsLoading">
      <!-- Top Stats Row -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Card>
            <Statistic
              title="在线设备"
              :value="onlineDevices"
              :suffix="`/ ${totalDevices}`"
              :value-style="{ color: '#1890ff' }"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="今日采集"
              :value="todayCollections"
              :value-style="{ color: '#52c41a' }"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="活跃告警"
              :value="activeAlarms"
              :value-style="{
                color: activeAlarms > 0 ? '#ff4d4f' : '#52c41a',
              }"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="运行任务"
              :value="runningTasks"
              :value-style="{ color: '#722ed1' }"
            />
          </Card>
        </Col>
      </Row>
    </Spin>

    <!-- Chart + Recent Alarms Row -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="14">
        <Card :bordered="false" title="采集成功率趋势">
          <Spin :spinning="trendLoading">
            <EchartsUI ref="trendChartRef" height="300px" />
          </Spin>
        </Card>
      </Col>
      <Col :span="10">
        <Card :bordered="false" title="最近告警">
          <template #extra>
            <router-link to="/dashboard/workspace">
              <Button type="link" size="small">查看全部</Button>
            </router-link>
          </template>
          <Table
            :columns="alarmColumns"
            :data-source="recentAlarms"
            :loading="alarmsLoading"
            :pagination="false"
            size="small"
            row-key="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'alarm_type'">
                <Tag>
                  {{ typeMap[record.alarm_type] || record.alarm_type }}
                </Tag>
              </template>
              <template v-if="column.key === 'severity'">
                <Tag
                  :color="severityMap[record.severity]?.color ?? 'default'"
                >
                  {{
                    severityMap[record.severity]?.text ?? record.severity
                  }}
                </Tag>
              </template>
            </template>
          </Table>
        </Card>
      </Col>
    </Row>

    <!-- Project Progress Table -->
    <Card :bordered="false" title="项目进度">
      <template #extra>
        <router-link to="/devices/meters">
          <Button type="link" size="small">管理设备</Button>
        </router-link>
      </template>
      <Table
        :columns="projectColumns"
        :data-source="projects"
        :loading="projectsLoading"
        :pagination="false"
        size="small"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'progress'">
            <Progress
              :percent="record.progress"
              :size="'small'"
              :status="record.progress >= 100 ? 'success' : undefined"
            />
          </template>
          <template v-if="column.key === 'status'">
            <Tag
              :color="
                record.status === 'completed'
                  ? 'green'
                  : record.status === 'testing'
                    ? 'blue'
                    : 'default'
              "
            >
              {{
                record.status === 'completed'
                  ? '已完成'
                  : record.status === 'testing'
                    ? '测试中'
                    : record.status === 'active'
                      ? '进行中'
                      : record.status ?? '-'
              }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
