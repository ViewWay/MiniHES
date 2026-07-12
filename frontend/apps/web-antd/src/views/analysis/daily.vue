<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { nextTick, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  message,
  Row,
  Select,
  Statistic,
  Table,
  TabPane,
  Tabs,
  Tag,
} from 'ant-design-vue';
import dayjs from 'dayjs';

import {
  exportDailyReport,
  getDailyAnalysis,
  getDailyMeters,
} from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const exporting = ref(false);
const analysisData = ref<any>(null);

const selectedProject = ref<number | undefined>(undefined);
const selectedMeter = ref<number | undefined>(undefined);
const dateRange = ref<[dayjs.Dayjs, dayjs.Dayjs] | undefined>([
  dayjs('2025-03-01'),
  dayjs('2025-06-01'),
]);

const projectOptions = ref<{ label: string; value: number }[]>([]);
const meterOptions = ref<{ label: string; value: number }[]>([]);
const metersLoading = ref(false);

const activeTab = ref('overview');

// ---------- Chart refs ----------
// Overview
const energyChartRef = ref<EchartsUIType>();
const { renderEcharts: renderEnergyChart } = useEcharts(energyChartRef);

const cumulativeChartRef = ref<EchartsUIType>();
const { renderEcharts: renderCumulativeChart } = useEcharts(cumulativeChartRef);

// Phase
const phaseVoltageChartRef = ref<EchartsUIType>();
const { renderEcharts: renderPhaseVoltageChart } = useEcharts(
  phaseVoltageChartRef,
);

const phaseCurrentChartRef = ref<EchartsUIType>();
const { renderEcharts: renderPhaseCurrentChart } = useEcharts(
  phaseCurrentChartRef,
);

// Load
const loadChartRef = ref<EchartsUIType>();
const { renderEcharts: renderLoadChart } = useEcharts(loadChartRef);

// Billing
const ratePieChartRef = ref<EchartsUIType>();
const { renderEcharts: renderRatePieChart } = useEcharts(ratePieChartRef);

const billingDailyChartRef = ref<EchartsUIType>();
const { renderEcharts: renderBillingDailyChart } = useEcharts(
  billingDailyChartRef,
);

const billingMonthlyChartRef = ref<EchartsUIType>();
const { renderEcharts: renderBillingMonthlyChart } = useEcharts(
  billingMonthlyChartRef,
);

const eepromChartRef = ref<EchartsUIType>();
const { renderEcharts: renderEepromChart } = useEcharts(eepromChartRef);

const stackChartRef = ref<EchartsUIType>();
const { renderEcharts: renderStackChart } = useEcharts(stackChartRef);

watchThemeAndRerender(renderAllCharts);

// ---------- Data helpers ----------
function fmt(v: any): string {
  if (v === null || v === undefined || v === '') return '-';
  if (typeof v === 'number') {
    return Number.isInteger(v) ? String(v) : v.toFixed(2);
  }
  return String(v);
}

// ---------- Projects / Meters ----------
async function fetchProjects() {
  try {
    const res = await getProjectList();
    const allProjects = res.items || res || [];
    projectOptions.value = allProjects.map((item: any) => ({
      label: item.name,
      value: item.id,
    }));
    // Auto-select first DCPP project
    const dcppProject = allProjects.find(
      (p: any) => p.name?.includes('DCPP') || p.name?.includes('DailyCheck'),
    );
    if (dcppProject) {
      selectedProject.value = dcppProject.id;
    }
  } catch (error) {
    console.error('[daily] fetchProjects failed', error);
  }
}

async function fetchMeters(projectId?: number) {
  metersLoading.value = true;
  selectedMeter.value = undefined;
  try {
    const res = await getDailyMeters(
      projectId ? { project_id: projectId } : undefined,
    );
    meterOptions.value = (res.items || []).map((m: any) => ({
      label: `${m.serial_number} - ${m.meter_name}`,
      value: m.id,
    }));
    if (meterOptions.value.length > 0 && meterOptions.value[0]) {
      selectedMeter.value = meterOptions.value[0].value;
      // Auto-trigger query
      await handleSearch();
    }
  } catch (error) {
    console.error('[daily] fetchMeters failed', error);
    meterOptions.value = [];
  } finally {
    metersLoading.value = false;
  }
}

async function handleSearch() {
  if (!selectedMeter.value) {
    message.warning('请先选择设备');
    return;
  }
  loading.value = true;
  try {
    const [startDate, endDate] = dateRange.value || [];
    analysisData.value = await getDailyAnalysis({
      meter_id: selectedMeter.value,
      date_from: startDate?.format('YYYY-MM-DD') || '',
      date_to: endDate?.format('YYYY-MM-DD') || '',
    });
    await nextTick();
    renderAllCharts();
  } catch {
    message.error('查询失败');
  } finally {
    loading.value = false;
  }
}

// ---------- Tab change ----------
function handleTabChange(key: number | string) {
  activeTab.value = String(key);
  void nextTick(() => {
    renderAllCharts();
  });
}

// ---------- Charts ----------
function renderAllCharts() {
  const data = analysisData.value;
  if (!data) return;

  switch (activeTab.value) {
    case 'billing': {
      renderRatePieChart(buildRatePieOption(data));
      renderBillingDailyChart(buildBillingDailyOption(data));
      renderBillingMonthlyChart(buildBillingMonthlyOption(data));
      break;
    }
    case 'load': {
      renderLoadChart(buildLoadChartOption(data));
      break;
    }
    case 'overview': {
      renderEnergyChart(buildEnergyChartOption(data));
      renderCumulativeChart(buildCumulativeChartOption(data));
      break;
    }
    case 'phase': {
      renderPhaseVoltageChart(buildPhaseVoltageOption(data));
      renderPhaseCurrentChart(buildPhaseCurrentOption(data));
      break;
    }
    case 'diagnostic': {
      renderEepromChart(buildEepromOption(data));
      renderStackChart(buildStackOption(data));
      break;
    }
  }
}

function buildEnergyChartOption(data: any): any {
  const trend = data.energy_trend || {};
  return {
    title: {
      text: '每日用电增量趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      data: trend.labels || [],
      axisLabel: { rotate: 30 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: '增量' }),
    series: [
      {
        name: '日增量',
        type: 'bar',
        data: trend.increases || [],
        itemStyle: { color: '#5470c6' },
      },
    ],
  };
}

function buildCumulativeChartOption(data: any): any {
  const trend = data.energy_trend || {};
  return {
    title: {
      text: '累计电能趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ bottom: 0, data: ['累计电能'] }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 40,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      boundaryGap: false,
      data: trend.labels || [],
      axisLabel: { rotate: 30 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: 'kWh' }),
    series: [
      {
        name: '累计电能',
        type: 'line',
        smooth: true,
        data: trend.cumulative || [],
        itemStyle: { color: '#91cc75' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  };
}

function buildPhaseVoltageOption(data: any): any {
  const phase = data.phase_data || {};
  const voltage = phase.voltage || {};
  return {
    title: {
      text: '三相电压对比',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      data: ['L1', 'L2', 'L3'],
    }),
    yAxis: themedAxis('y', { type: 'value', name: '电压(V)' }),
    series: [
      {
        name: '电压',
        type: 'bar',
        data: [
          voltage.l1 ?? null,
          voltage.l2 ?? null,
          voltage.l3 ?? null,
        ],
        itemStyle: { color: '#5470c6' },
        label: { show: true, position: 'top', formatter: '{c}' },
      },
    ],
  };
}

function buildPhaseCurrentOption(data: any): any {
  const phase = data.phase_data || {};
  const current = phase.current || {};
  return {
    title: {
      text: '三相电流对比',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      data: ['L1', 'L2', 'L3'],
    }),
    yAxis: themedAxis('y', { type: 'value', name: '电流(A)' }),
    series: [
      {
        name: '电流',
        type: 'bar',
        data: [
          current.l1 ?? null,
          current.l2 ?? null,
          current.l3 ?? null,
        ],
        itemStyle: { color: '#ee6666' },
        label: { show: true, position: 'top', formatter: '{c}' },
      },
    ],
  };
}

function buildLoadChartOption(data: any): any {
  const load = data.load_profile || {};
  return {
    title: {
      text: '日负荷曲线',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({
      trigger: 'axis',
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return '';
        const p = params[0];
        const label = Array.isArray(load.labels) ? load.labels[p.dataIndex] : '';
        const val =
          p.value === null || p.value === undefined ? '-' : p.value.toFixed(3);
        return `${label}<br/>负荷: ${val} kW`;
      },
    }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      boundaryGap: false,
      data: load.labels || [],
      axisLabel: {
        interval: Math.max(
          1,
          Math.floor(((load.labels || []).length - 1) / 12),
        ),
        rotate: 0,
      },
    }),
    yAxis: themedAxis('y', { type: 'value', name: '功率(kW)' }),
    series: [
      {
        name: '负荷',
        type: 'line',
        showSymbol: false,
        smooth: true,
        data: load.values || [],
        itemStyle: { color: '#73c0de' },
        areaStyle: { opacity: 0.15 },
      },
    ],
  };
}

function buildRatePieOption(data: any): any {
  const billing = data.billing || {};
  const rates = billing.rates || {};
  return {
    title: {
      text: '费率分布',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    }),
    legend: themedLegend({ bottom: 0 }),
    series: [
      {
        name: '费率',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        data: [
          { name: '费率1', value: rates.rate1 ?? 0 },
          { name: '费率2', value: rates.rate2 ?? 0 },
          { name: '反向输出', value: rates.export ?? 0 },
        ].filter((d) => d.value !== null && d.value !== undefined),
        label: { formatter: '{b}: {d}%' },
      },
    ],
  };
}

function buildBillingDailyOption(data: any): any {
  const billing = data.billing || {};
  const daily = billing.daily || {};
  return {
    title: {
      text: '日计费趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      boundaryGap: false,
      data: daily.labels || [],
      axisLabel: { rotate: 30 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: '电能' }),
    series: [
      {
        name: '日计费',
        type: 'line',
        showSymbol: false,
        smooth: true,
        data: daily.values || [],
        itemStyle: { color: '#fac858' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  };
}

function buildBillingMonthlyOption(data: any): any {
  const billing = data.billing || {};
  const monthly = billing.monthly || {};
  return {
    title: {
      text: '月计费对比',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      data: monthly.labels || [],
    }),
    yAxis: themedAxis('y', { type: 'value', name: '电能' }),
    series: [
      {
        name: '月计费',
        type: 'bar',
        data: monthly.values || [],
        itemStyle: { color: '#91cc75' },
      },
    ],
  };
}

// ---------- Export ----------
function buildEepromOption(data: any): any {
  const diag = data.diagnostic || {};
  const eeprom = diag.eeprom || {};
  const zones = eeprom.zones || [];
  return {
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: { top: 40, bottom: 30, left: 60, right: 20, containLabel: true },
    xAxis: themedAxis('x', {
      type: 'category',
      data: zones.map((z: any) => `区${z.zone}`),
      axisLabel: { interval: 3 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: '写入次数' }),
    series: [
      {
        name: '写入次数',
        type: 'bar',
        data: zones.map((z: any) => z.writes),
        itemStyle: {
          color: (params: any) =>
            params.value > 500 ? '#ff4d4f' : params.value > 100 ? '#faad14' : '#52c41a',
        },
      },
    ],
  };
}

function buildStackOption(data: any): any {
  const diag = data.diagnostic || {};
  const stack = diag.stack || {};
  const modules = stack.modules || [];
  return {
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ data: ['已用', '总量'] }),
    grid: { top: 40, bottom: 30, left: 60, right: 20, containLabel: true },
    xAxis: themedAxis('x', {
      type: 'category',
      data: modules.map((m: any) => m.name),
    }),
    yAxis: themedAxis('y', { type: 'value', name: '字节' }),
    series: [
      {
        name: '已用',
        type: 'bar',
        data: modules.map((m: any) => m.used),
        itemStyle: { color: '#5470c6' },
      },
      {
        name: '总量',
        type: 'bar',
        data: modules.map((m: any) => m.total_size),
        itemStyle: { color: '#91cc75' },
      },
    ],
  };
}

async function handleExport() {
  if (!selectedMeter.value) {
    message.warning('请先选择设备');
    return;
  }
  exporting.value = true;
  try {
    const [startDate, endDate] = dateRange.value || [];
    const blob: Blob = await exportDailyReport({
      meter_id: selectedMeter.value,
      date_from: startDate?.format('YYYY-MM-DD') || '',
      date_to: endDate?.format('YYYY-MM-DD') || '',
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `日线分析_${selectedMeter.value}.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败');
  } finally {
    exporting.value = false;
  }
}

// ---------- Detail tables ----------
const overviewColumns = [
  { title: '日期', dataIndex: 'date', width: 110 },
  { title: '累计电能', dataIndex: 'total_energy', width: 110 },
  { title: '日增量', dataIndex: 'daily_increase', width: 90 },
  { title: 'L1电压(V)', dataIndex: 'voltage_l1', width: 90 },
  { title: 'L2电压(V)', dataIndex: 'voltage_l2', width: 90 },
  { title: 'L3电压(V)', dataIndex: 'voltage_l3', width: 90 },
  { title: '总功率(W)', dataIndex: 'power_total', width: 100 },
  { title: '完整率', key: 'completeness', width: 90 },
  { title: '状态', key: 'status', width: 80 },
];

// Phase table: rows = measurement items, cols = L1/L2/L3/总计
const phaseTableRows = ref<any[]>([]);
const phaseColumns = ref<any[]>([]);

function buildPhaseTable(data: any) {
  const phase = data.phase_data || {};
  const v = phase.voltage || {};
  const c = phase.current || {};
  const ap = phase.active_power || {};
  const rp = phase.reactive_power || {};
  const sp = phase.apparent_power || {};

  phaseColumns.value = [
    { title: '项目', dataIndex: 'name', width: 140 },
    { title: 'L1', dataIndex: 'l1', width: 100 },
    { title: 'L2', dataIndex: 'l2', width: 100 },
    { title: 'L3', dataIndex: 'l3', width: 100 },
    { title: '总计', dataIndex: 'total', width: 100 },
  ];

  phaseTableRows.value = [
    {
      key: 'voltage',
      name: '电压(V)',
      l1: fmt(v.l1),
      l2: fmt(v.l2),
      l3: fmt(v.l3),
      total: '-',
    },
    {
      key: 'current',
      name: '电流(A)',
      l1: fmt(c.l1),
      l2: fmt(c.l2),
      l3: fmt(c.l3),
      total: '-',
    },
    {
      key: 'active_power',
      name: '有功功率(W)',
      l1: fmt(ap.l1),
      l2: fmt(ap.l2),
      l3: fmt(ap.l3),
      total: fmt(ap.total),
    },
    {
      key: 'reactive_power',
      name: '无功功率(var)',
      l1: fmt(rp.l1),
      l2: fmt(rp.l2),
      l3: fmt(rp.l3),
      total: fmt(rp.total),
    },
    {
      key: 'apparent_power',
      name: '视在功率(VA)',
      l1: '-',
      l2: '-',
      l3: '-',
      total: fmt(sp.total),
    },
  ];
}

const eventColumns = [
  { title: '事件名称', dataIndex: 'name', width: 200 },
  { title: '类型', dataIndex: 'code', width: 160 },
  { title: '时间', dataIndex: 'timestamp' },
];

const stackColumns = [
  { title: '任务模块', dataIndex: 'name', width: 120 },
  { title: '已用(B)', dataIndex: 'used', width: 100 },
  { title: '总量(B)', dataIndex: 'total_size', width: 100 },
  { title: '峰值(B)', dataIndex: 'peak', width: 100 },
  { title: '使用率', key: 'usage_pct', width: 100 },
];

// ---------- Watch ----------
watch(selectedProject, (val) => {
  fetchMeters(val);
});

watch(analysisData, (val) => {
  if (val) buildPhaseTable(val);
});

onMounted(() => {
  fetchProjects();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="每日数据分析" style="margin-bottom: 16px">
      <template #extra>
        <Button
          :loading="exporting"
          :disabled="!analysisData"
          @click="handleExport"
        >
          导出CSV
        </Button>
      </template>
      <Form layout="inline">
        <Form.Item label="项目">
          <Select
            v-model:value="selectedProject"
            allow-clear
            placeholder="全部项目"
            style="width: 200px"
            :options="projectOptions"
          />
        </Form.Item>
        <Form.Item label="设备">
          <Select
            v-model:value="selectedMeter"
            placeholder="选择设备"
            style="width: 220px"
            :options="meterOptions"
            :loading="metersLoading"
            show-search
            option-filter-prop="label"
          />
        </Form.Item>
        <Form.Item label="日期范围">
          <RangePicker
            v-model:value="dateRange"
            style="width: 260px"
            :presets="[
              {
                label: '近7天',
                value: [dayjs().subtract(7, 'day'), dayjs()],
              },
              {
                label: '近30天',
                value: [dayjs().subtract(30, 'day'), dayjs()],
              },
              {
                label: '近90天',
                value: [dayjs().subtract(90, 'day'), dayjs()],
              },
              {
                label: '近一年',
                value: [dayjs().subtract(1, 'year'), dayjs()],
              },
            ]"
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" :loading="loading" @click="handleSearch">
            查询分析
          </Button>
        </Form.Item>
      </Form>
    </Card>

    <template v-if="analysisData">
      <Card
        v-if="analysisData.summary?.demo"
        :bordered="false"
        style="margin-bottom: 16px"
        :body-style="{ padding: '8px 16px' }"
      >
        <Tag color="orange">无数据</Tag>
        <span style="margin-left: 8px; color: #999; font-size: 12px">
          该设备在所选日期范围内无采集数据
        </span>
      </Card>

      <Tabs
        v-else
        v-model:active-key="activeTab"
        :destroy-inactive-tab-pane="false"
        @change="handleTabChange"
      >
        <!-- ============== Tab 1: 概览 ============== -->
        <TabPane key="overview" tab="概览">
          <Row :gutter="16" style="margin-bottom: 16px">
            <Col :span="6">
              <Card>
                <Statistic
                  title="采集天数"
                  :value="analysisData.summary?.days_collected"
                  suffix="天"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="日均增量"
                  :value="analysisData.summary?.avg_daily_increase"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="累计增量"
                  :value="analysisData.summary?.total_increase"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="最新电能"
                  :value="analysisData.summary?.latest_energy"
                />
              </Card>
            </Col>
          </Row>

          <Card :bordered="false" title="每日用电增量趋势" style="margin-bottom: 16px">
            <EchartsUI ref="energyChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="累计电能趋势" style="margin-bottom: 16px">
            <EchartsUI ref="cumulativeChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="每日采集明细">
            <Table
              :columns="overviewColumns"
              :data-source="analysisData.daily_records || []"
              row-key="date"
              size="middle"
              :pagination="{
                pageSize: 15,
                showTotal: (t: number) => `共 ${t} 条`,
              }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'completeness'">
                  <Tag
                    :color="
                      record.completeness >= 95
                        ? 'green'
                        : record.completeness >= 80
                          ? 'orange'
                          : 'red'
                    "
                  >
                    {{ record.completeness }}%
                  </Tag>
                </template>
                <template v-else-if="column.key === 'status'">
                  <Tag :color="record.status === 'success' ? 'green' : 'orange'">
                    {{ record.status === 'success' ? '成功' : record.status }}
                  </Tag>
                </template>
                <template v-else-if="record[column.dataIndex as string] === null">
                  <span style="color: #999">-</span>
                </template>
              </template>
            </Table>
          </Card>
        </TabPane>

        <!-- ============== Tab 2: 三相数据 ============== -->
        <TabPane key="phase" tab="三相数据">
          <Row :gutter="16" style="margin-bottom: 16px">
            <Col :span="12">
              <Card>
                <Statistic
                  title="电压不平衡度"
                  :value="analysisData.phase_data?.voltage_unbalance"
                  :precision="2"
                  suffix="%"
                />
              </Card>
            </Col>
            <Col :span="12">
              <Card>
                <Statistic
                  title="电流不平衡度"
                  :value="analysisData.phase_data?.current_unbalance"
                  :precision="2"
                  suffix="%"
                />
              </Card>
            </Col>
          </Row>

          <Card :bordered="false" title="三相电压对比" style="margin-bottom: 16px">
            <EchartsUI ref="phaseVoltageChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="三相电流对比" style="margin-bottom: 16px">
            <EchartsUI ref="phaseCurrentChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="三相详细数据">
            <Table
              :columns="phaseColumns"
              :data-source="phaseTableRows"
              row-key="key"
              size="middle"
              :pagination="false"
            />
          </Card>
        </TabPane>

        <!-- ============== Tab 3: 负荷曲线 ============== -->
        <TabPane key="load" tab="负荷曲线">
          <Row :gutter="16" style="margin-bottom: 16px">
            <Col :span="6">
              <Card>
                <Statistic
                  title="峰值(kW)"
                  :value="analysisData.load_profile?.stats?.peak"
                  :precision="3"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="谷值(kW)"
                  :value="analysisData.load_profile?.stats?.valley"
                  :precision="3"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="平均(kW)"
                  :value="analysisData.load_profile?.stats?.average"
                  :precision="3"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="峰谷差(kW)"
                  :value="analysisData.load_profile?.stats?.peak_valley_diff"
                  :precision="3"
                />
              </Card>
            </Col>
          </Row>

          <Card :bordered="false" title="日负荷曲线（96点）">
            <EchartsUI ref="loadChartRef" height="300px" />
          </Card>
        </TabPane>

        <!-- ============== Tab 4: 计费数据 ============== -->
        <TabPane key="billing" tab="计费数据">
          <Card :bordered="false" title="费率分布" style="margin-bottom: 16px">
            <EchartsUI ref="ratePieChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="日计费趋势" style="margin-bottom: 16px">
            <EchartsUI ref="billingDailyChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="月计费对比">
            <EchartsUI ref="billingMonthlyChartRef" height="300px" />
          </Card>
        </TabPane>

        <!-- ============== Tab 5: 事件日志 ============== -->
        <TabPane key="events" tab="事件日志">
          <Card :bordered="false" title="事件记录">
            <Table
              v-if="(analysisData.events || []).length > 0"
              :columns="eventColumns"
              :data-source="analysisData.events || []"
              row-key="timestamp"
              size="middle"
              :pagination="{ pageSize: 15 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'code'">
                  <Tag color="blue">{{ record.code || '-' }}</Tag>
                </template>
              </template>
            </Table>
            <Empty
              v-else
              description="无事件记录"
              style="padding: 60px 0"
            />
          </Card>
        </TabPane>

        <TabPane key="diagnostic" tab="诊断数据">
          <Row :gutter="16" style="margin-bottom: 16px">
            <Col :span="6">
              <Card>
                <Statistic
                  title="EEPROM 总写入"
                  :value="analysisData.diagnostic?.eeprom?.total_writes ?? 0"
                  :value-style="{ color: analysisData.diagnostic?.eeprom?.status_color || '#52c41a' }"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="EEPROM 状态"
                  :value="analysisData.diagnostic?.eeprom?.status ?? '-'"
                  :value-style="{ color: analysisData.diagnostic?.eeprom?.status_color || '#52c41a' }"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="活跃区域"
                  :value="analysisData.diagnostic?.eeprom?.active_zones ?? 0"
                  suffix="/ 42"
                />
              </Card>
            </Col>
            <Col :span="6">
              <Card>
                <Statistic
                  title="堆栈使用率"
                  :value="analysisData.diagnostic?.stack?.heap?.overall_usage_pct ?? 0"
                  suffix="%"
                />
              </Card>
            </Col>
          </Row>

          <Card :bordered="false" title="EEPROM 各区域写入次数" style="margin-bottom: 16px">
            <EchartsUI ref="eepromChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="任务堆栈内存使用" style="margin-bottom: 16px">
            <EchartsUI ref="stackChartRef" height="300px" />
          </Card>

          <Card :bordered="false" title="堆栈模块明细">
            <Table
              :columns="stackColumns"
              :data-source="analysisData.diagnostic?.stack?.modules || []"
              row-key="name"
              size="middle"
              :pagination="false"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'usage_pct'">
                  <Tag
                    :color="record.usage_pct >= 80 ? 'red' : record.usage_pct >= 60 ? 'orange' : 'green'"
                  >
                    {{ record.usage_pct }}%
                  </Tag>
                </template>
              </template>
            </Table>
          </Card>
        </TabPane>
      </Tabs>
    </template>

    <Card v-else :bordered="false">
      <div style="text-align: center; padding: 60px; color: #999">
        请选择项目和设备后点击「查询分析」
      </div>
    </Card>
  </Page>
</template>
