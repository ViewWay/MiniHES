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
import { useChartTheme } from '#/composables/useChartTheme';

const { chartColors, themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } = useChartTheme();
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

async function fetchData() {
  loading.value = true;
  try {
    const projectResp = await getProjectDetail(projectId.value);
    projectInfo.value = projectResp;

    const meterResp = await getMeterList({
      project_id: projectId.value,
      page: 1,
      page_size: 200,
    });
    const items = meterResp?.items ?? meterResp ?? [];
    meters.value = Array.isArray(items) ? items : [];

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
  const c = chartColors.value;
  const hourLabels = generateHourLabels(24);

  const topMeters = meters.value.slice(0, 5);
  const energySeries = topMeters.map((m) => ({
    name: m.meter_name || m.serial_number || `Meter ${m.id}`,
    type: 'line' as const,
    smooth: true,
    data: [],
  }));

  renderEnergyChart({
    tooltip: themedTooltip(),
    legend: themedLegend({
      data: topMeters.map(
        (m) => m.meter_name || m.serial_number || `Meter ${m.id}`,
      ),
      top: 0,
    }),
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: themedAxis('x', { type: 'category', data: hourLabels }),
    yAxis: themedAxis('y', { type: 'value', name: 'kWh' }),
    series: energySeries,
  });

  renderCommChart({
    tooltip: themedTooltip({ trigger: 'item' }),
    legend: themedLegend({ orient: 'vertical', left: 'left' }),
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        data: [
          { value: onlineCount.value, name: '在线', itemStyle: { color: '#52c41a' } },
          { value: offlineCount.value, name: '离线', itemStyle: { color: '#ff4d4f' } },
        ],
        label: { color: c.text },
      },
    ],
  });

  const stackMeters = meters.value.slice(0, 10);
  const stackNames = stackMeters.map(
    (m) => m.meter_name || m.serial_number || `#${m.id}`,
  );
  const stackValues = stackMeters.map((m) => m.stack_usage ?? 0);

  renderStackChart({
    tooltip: themedTooltip({ axisPointer: { type: 'shadow' } }),
    grid: { top: 10, bottom: 30, left: 100, right: 30 },
    xAxis: themedAxis('x', {
      type: 'value',
      max: 100,
      axisLabel: { color: c.text, formatter: '{value}%' },
    }),
    yAxis: themedAxis('y', {
      type: 'category',
      data: stackNames,
    }),
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
          color: c.textSecondary,
          fontSize: 11,
        },
      },
    ],
  });

  renderPqChart({
    tooltip: themedTooltip(),
    legend: themedLegend({ data: ['电压A', '电压B', '电压C'], top: 0 }),
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: themedAxis('x', { type: 'category', data: hourLabels }),
    yAxis: themedAxis('y', { type: 'value', name: 'V', min: 200, max: 240 }),
    series: [
      { name: '电压A', type: 'line', smooth: true, data: [], itemStyle: { color: '#5470c6' } },
      { name: '电压B', type: 'line', smooth: true, data: [], itemStyle: { color: '#91cc75' } },
      { name: '电压C', type: 'line', smooth: true, data: [], itemStyle: { color: '#fac858' } },
    ],
  });
}

onMounted(async () => {
  await fetchData();
  renderCharts();
  watchThemeAndRerender(renderCharts);
});

</script>

<template>
  <Page auto-content-height>
      <div style="margin-bottom: 16px; display: flex; align-items: center">
        <Button type="link" @click="router.push('/screen/overview')">← 返回概览</Button>
        <span style="font-size: 16px; font-weight: 600; margin-left: 8px">
          {{ projectInfo.name || `项目 #${projectId}` }} - 详情大屏
        </span>
      </div>

      <Spin :spinning="loading">
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="设备总数" :value="meterCount" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="在线设备" :value="onlineCount" :value-style="{ color: '#52c41a' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="离线设备" :value="offlineCount" :value-style="{ color: '#ff4d4f' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="在线率" :value="onlineRate" suffix="%" :value-style="{ color: '#69b1ff' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="堆栈告警" :value="stackAlertCount" :value-style="{ color: '#faad14' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="活跃事件" :value="eventStats.reduce((s, e) => s + e.count, 0)" :value-style="{ color: '#ff7a45' }" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="16">
            <Card title="能耗曲线" :bordered="false">
              <EchartsUI ref="energyChartRef" height="300px" />
            </Card>
          </Col>
          <Col :span="8">
            <Card title="通信状态" :bordered="false" style="margin-bottom: 16px">
              <EchartsUI ref="commChartRef" height="300px" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="12">
            <Card title="堆栈监控" :bordered="false">
              <EchartsUI ref="stackChartRef" height="300px" />
            </Card>
          </Col>
          <Col :span="12">
            <Card title="电能质量曲线" :bordered="false">
              <EchartsUI ref="pqChartRef" height="300px" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6" v-for="e in eventStats" :key="e.type">
            <Card :bordered="false">
              <Statistic :title="e.type" :value="e.count" :value-style="{ color: e.color }" />
            </Card>
          </Col>
        </Row>

        <Card title="设备列表" :bordered="false">
          <Table
            :columns="columns"
            :data-source="meters"
            row-key="id"
            :pagination="false"
            size="middle"
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
                <a @click="router.push(`/screen/meter/${record.id}`)">
                  单表监控 →
                </a>
              </template>
            </template>
          </Table>
        </Card>
      </Spin>
  </Page>
</template>
