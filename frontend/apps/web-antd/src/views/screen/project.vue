<script setup lang="ts">
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Badge,
  Button,
  Card,
  Col,
  Progress,
  Row,
  Spin,
  Statistic,
  Table,
} from 'ant-design-vue';

import { getMeterList } from '#/api/modules/meter';
import { getProjectDetail } from '#/api/modules/project';

const route = useRoute();
const router = useRouter();
const projectId = ref(Number(route.query.id) || 0);

const loading = ref(true);
const projectInfo = ref<Record<string, any>>({});
const meters = ref<any[]>([]);
const eventStats = ref([
  { type: '标准事件', count: 0, color: '#1890ff' },
  { type: '窃电事件', count: 0, color: '#ff4d4f' },
  { type: '通信事件', count: 0, color: '#fa8c16' },
  { type: '预付费事件', count: 0, color: '#13c2c2' },
]);

// Computed statistics
const meterCount = computed(() => meters.value.length);
const onlineCount = computed(
  () => meters.value.filter((m) => m.is_online).length,
);
const offlineCount = computed(() => meterCount.value - onlineCount.value);
const stackAlertCount = computed(
  () => meters.value.filter((m) => (m.stack_usage ?? 0) > 80).length,
);
const onlineRate = computed(() =>
  meterCount.value > 0
    ? Number(((onlineCount.value / meterCount.value) * 100).toFixed(1))
    : 0,
);

const columns = [
  { title: '编号', dataIndex: 'serial_number', width: 120 },
  { title: '名称', dataIndex: 'meter_name', width: 120 },
  { title: '类型', dataIndex: 'meter_type_id', width: 80 },
  { title: '在线', dataIndex: 'is_online', key: 'online', width: 80 },
  { title: '最后通信', dataIndex: 'last_comm_time', width: 180 },
  {
    title: '堆栈使用率',
    dataIndex: 'stack_usage',
    key: 'stack_usage',
    width: 120,
  },
  { title: '操作', key: 'action', width: 100 },
];

// Chart refs
const energyChartRef = ref<EchartsUIType>();
const commChartRef = ref<EchartsUIType>();
const stackChartRef = ref<EchartsUIType>();
const pqChartRef = ref<EchartsUIType>();

const { renderEcharts: renderEnergyChart } = useEcharts(energyChartRef);
const { renderEcharts: renderCommChart } = useEcharts(commChartRef);
const { renderEcharts: renderStackChart } = useEcharts(stackChartRef);
const { renderEcharts: renderPqChart } = useEcharts(pqChartRef);

function stackColor(value: number) {
  if (value >= 80) return '#ff4d4f';
  if (value >= 60) return '#faad14';
  return '#52c41a';
}

function generateHourLabels(count: number) {
  const labels: string[] = [];
  const now = new Date();
  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 3600 * 1000);
    labels.push(`${String(d.getHours()).padStart(2, '0')}:00`);
  }
  return labels;
}

function generateMockSeries(
  count: number,
  base: number,
  variance: number,
): number[] {
  return Array.from({ length: count }, () =>
    Number((base + (Math.random() - 0.5) * 2 * variance).toFixed(2)),
  );
}

async function fetchData() {
  loading.value = true;
  try {
    // Fetch project detail
    const projectResp = await getProjectDetail(projectId.value);
    projectInfo.value = projectResp;

    // Fetch meters for this project
    const meterResp = await getMeterList({
      project_id: projectId.value,
      page: 1,
      page_size: 200,
    });
    const items = meterResp?.items ?? meterResp ?? [];
    meters.value = Array.isArray(items) ? items : [];

    // Aggregate event stats from project data
    const events = projectInfo.value?.events ?? [];
    if (Array.isArray(events) && events.length > 0) {
      const grouped: Record<string, number> = {};
      for (const e of events) {
        const t = e.type || '标准事件';
        grouped[t] = (grouped[t] || 0) + 1;
      }
      eventStats.value = eventStats.value.map((s) => ({
        ...s,
        count: grouped[s.type] ?? 0,
      }));
    }
  } catch {
    // API not available; keep empty data for graceful degradation
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  const hourLabels = generateHourLabels(24);

  // --- Energy curve chart (multi-line for top 5 meters) ---
  // TODO: Replace generateMockSeries with real data from InfluxDB API when available
  const topMeters = meters.value.slice(0, 5);
  const energySeries = topMeters.map((m) => ({
    name: m.meter_name || m.serial_number || `Meter ${m.id}`,
    type: 'line' as const,
    smooth: true,
    data: generateMockSeries(24, 2.5, 1.0),
  }));

  renderEnergyChart({
    tooltip: { trigger: 'axis' },
    legend: {
      data: topMeters.map(
        (m) => m.meter_name || m.serial_number || `Meter ${m.id}`,
      ),
      top: 0,
      textStyle: { color: '#ccc' },
    },
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: hourLabels,
      axisLabel: { color: '#aaa' },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'kWh',
      nameTextStyle: { color: '#aaa' },
      axisLabel: { color: '#aaa' },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: energySeries,
  });

  // --- Communication status chart (online/offline pie) ---
  renderCommChart({
    tooltip: { trigger: 'item' },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { color: '#ccc' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        data: [
          {
            value: onlineCount.value,
            name: '在线',
            itemStyle: { color: '#52c41a' },
          },
          {
            value: offlineCount.value,
            name: '离线',
            itemStyle: { color: '#ff4d4f' },
          },
        ],
        label: { color: '#ccc' },
      },
    ],
  });

  // --- Stack monitoring chart (horizontal bar per meter) ---
  const stackMeters = meters.value.slice(0, 10);
  const stackNames = stackMeters.map(
    (m) => m.meter_name || m.serial_number || `#${m.id}`,
  );
  const stackValues = stackMeters.map((m) => m.stack_usage ?? 0);

  renderStackChart({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 10, bottom: 30, left: 100, right: 30 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#aaa', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#333' } },
    },
    yAxis: {
      type: 'category',
      data: stackNames,
      axisLabel: { color: '#aaa' },
    },
    series: [
      {
        type: 'bar',
        data: stackValues.map((v) => ({
          value: v,
          itemStyle: { color: stackColor(v) },
        })),
        barWidth: 14,
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: '#ccc',
          fontSize: 11,
        },
      },
    ],
  });

  // --- Power quality chart (voltage quality line) ---
  // TODO: Replace generateMockSeries with real data from InfluxDB API when available
  renderPqChart({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['电压A', '电压B', '电压C'],
      top: 0,
      textStyle: { color: '#ccc' },
    },
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: hourLabels,
      axisLabel: { color: '#aaa' },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'V',
      min: 200,
      max: 240,
      nameTextStyle: { color: '#aaa' },
      axisLabel: { color: '#aaa' },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: [
      {
        name: '电压A',
        type: 'line',
        smooth: true,
        data: generateMockSeries(24, 220, 3),
        itemStyle: { color: '#5470c6' },
      },
      {
        name: '电压B',
        type: 'line',
        smooth: true,
        data: generateMockSeries(24, 219, 3),
        itemStyle: { color: '#91cc75' },
      },
      {
        name: '电压C',
        type: 'line',
        smooth: true,
        data: generateMockSeries(24, 221, 3),
        itemStyle: { color: '#fac858' },
      },
    ],
  });
}

onMounted(async () => {
  await fetchData();
  renderCharts();
});
</script>

<template>
  <Page auto-content-height>
    <div style="background: #001529; min-height: 100vh; padding: 24px">
      <!-- Header -->
      <div style="margin-bottom: 16px">
        <Button type="text" style="color: #ccc" @click="router.push('/screen/overview')">← 返回概览</Button>
        <span style="color: #fff; font-size: 18px; font-weight: 600; margin-left: 16px">
          {{ projectInfo.name || `项目 #${projectId}` }} - 详情大屏
        </span>
      </div>

      <Spin :spinning="loading">
        <!-- Stats Row -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="设备总数" :value="meterCount" value-style="color: #fff" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="在线设备" :value="onlineCount" value-style="color: #52c41a" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="离线设备" :value="offlineCount" value-style="color: #ff4d4f" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="在线率" :value="onlineRate" suffix="%" value-style="color: #69b1ff" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="堆栈告警" :value="stackAlertCount" value-style="color: #faad14" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="活跃事件" :value="eventStats.reduce((s, e) => s + e.count, 0)" value-style="color: #ff7a45" />
            </Card>
          </Col>
        </Row>

        <!-- Charts Row 1: Energy + Communication -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="16">
            <Card
              title="能耗曲线"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="energyChartRef" height="320px" />
            </Card>
          </Col>
          <Col :span="8">
            <Card
              title="通信状态"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c; margin-bottom: 16px"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="commChartRef" height="320px" />
            </Card>
          </Col>
        </Row>

        <!-- Charts Row 2: Stack + Power Quality -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="12">
            <Card
              title="堆栈监控"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="stackChartRef" height="300px" />
            </Card>
          </Col>
          <Col :span="12">
            <Card
              title="电能质量曲线"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="pqChartRef" height="300px" />
            </Card>
          </Col>
        </Row>

        <!-- Event Statistics -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6" v-for="e in eventStats" :key="e.type">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic :title="e.type" :value="e.count" :value-style="{ color: e.color }" />
            </Card>
          </Col>
        </Row>

        <!-- Meter Table -->
        <Card
          title="设备列表"
          :bordered="false"
          style="background: #0c2340; border-color: #1a3a5c"
          :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
          :body-style="{ padding: '0' }"
        >
          <Table
            :columns="columns"
            :data-source="meters"
            row-key="id"
            :pagination="false"
            size="middle"
            style="background: transparent"
            :row-style="{ background: 'transparent' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'online'">
                <Badge
                  :status="record.is_online ? 'success' : 'error'"
                  :text="record.is_online ? '在线' : '离线'"
                />
              </template>
              <template v-if="column.key === 'stack_usage'">
                <Progress
                  :percent="record.stack_usage ?? 0"
                  :stroke-color="stackColor(record.stack_usage ?? 0)"
                  :size="'small'"
                />
              </template>
              <template v-if="column.key === 'action'">
                <a
                  style="color: #69b1ff"
                  @click="router.push(`/screen/meter/${record.id}`)"
                >
                  单表监控 →
                </a>
              </template>
            </template>
          </Table>
        </Card>
      </Spin>
    </div>
  </Page>
</template>
