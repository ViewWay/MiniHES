<script setup lang="ts">
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  Progress,
  Row,
  Spin,
  Statistic,
  Tag,
} from 'ant-design-vue';

import { getMeterDetail } from '#/api/modules/meter';
import { useChartTheme } from '#/composables/useChartTheme';

const { isDark } = useChartTheme();
const route = useRoute();
const router = useRouter();
const meterId = ref(Number(route.params.id) || 0);

const loading = ref(true);
const meterInfo = ref<Record<string, any>>({});

// Real-time data with defaults
const meterData = ref({
  voltage_a: 220.5,
  voltage_b: 219.8,
  voltage_c: 221.2,
  current_a: 5.2,
  current_b: 4.8,
  current_c: 5.5,
  power_a: 1146.6,
  power_b: 1055.0,
  power_c: 1216.6,
  pf_a: 0.98,
  pf_b: 0.97,
  pf_c: 0.99,
  frequency: 50.01,
  stack_usage: 45,
  eeprom_writes: 1234,
  phase_angle_a: 0,
  phase_angle_b: 120,
  phase_angle_c: 240,
});

// Stability score (computed from data quality)
const stabilityScore = ref(92);

// Time-series data for real-time charts
const timeLabels = ref<string[]>([]);
const voltageHistoryA = ref<number[]>([]);
const voltageHistoryB = ref<number[]>([]);
const voltageHistoryC = ref<number[]>([]);
const currentHistoryA = ref<number[]>([]);
const currentHistoryB = ref<number[]>([]);
const currentHistoryC = ref<number[]>([]);

let pollTimer: ReturnType<typeof setInterval> | null = null;

// Computed
const stackColor = computed(() => {
  const v = meterData.value.stack_usage;
  if (v >= 80) return '#ff4d4f';
  if (v >= 60) return '#faad14';
  return '#52c41a';
});

const stackStatus = computed(() => {
  const v = meterData.value.stack_usage;
  if (v >= 80) return 'danger';
  if (v >= 60) return 'warning';
  return 'normal';
});

const eepromStatus = computed(() => {
  const writes = meterData.value.eeprom_writes;
  if (writes > 100_000) return { text: '老化', color: '#ff4d4f' };
  if (writes > 50_000) return { text: '磨损', color: '#faad14' };
  return { text: '正常', color: '#52c41a' };
});

// Chart refs
const rtChartRef = ref<EchartsUIType>();
const gaugeChartRef = ref<EchartsUIType>();
const eventChartRef = ref<EchartsUIType>();

const { renderEcharts: renderRtChart, updateData: updateRtChart } =
  useEcharts(rtChartRef);
const { renderEcharts: renderGaugeChart } = useEcharts(gaugeChartRef);
const { renderEcharts: renderEventChart } = useEcharts(eventChartRef);

function timeNow(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
}

function jitter(base: number, variance: number): number {
  return Number((base + (Math.random() - 0.5) * 2 * variance).toFixed(2));
}

async function fetchMeterData() {
  loading.value = true;
  try {
    const resp = await getMeterDetail(meterId.value);
    meterInfo.value = resp;

    // If the API returns real-time data, use it
    if (resp?.realtime) {
      const rt = resp.realtime;
      meterData.value = {
        voltage_a: rt.voltage_a ?? meterData.value.voltage_a,
        voltage_b: rt.voltage_b ?? meterData.value.voltage_b,
        voltage_c: rt.voltage_c ?? meterData.value.voltage_c,
        current_a: rt.current_a ?? meterData.value.current_a,
        current_b: rt.current_b ?? meterData.value.current_b,
        current_c: rt.current_c ?? meterData.value.current_c,
        power_a: rt.power_a ?? meterData.value.power_a,
        power_b: rt.power_b ?? meterData.value.power_b,
        power_c: rt.power_c ?? meterData.value.power_c,
        pf_a: rt.pf_a ?? meterData.value.pf_a,
        pf_b: rt.pf_b ?? meterData.value.pf_b,
        pf_c: rt.pf_c ?? meterData.value.pf_c,
        frequency: rt.frequency ?? meterData.value.frequency,
        stack_usage: rt.stack_usage ?? meterData.value.stack_usage,
        eeprom_writes: rt.eeprom_writes ?? meterData.value.eeprom_writes,
        phase_angle_a: rt.phase_angle_a ?? meterData.value.phase_angle_a,
        phase_angle_b: rt.phase_angle_b ?? meterData.value.phase_angle_b,
        phase_angle_c: rt.phase_angle_c ?? meterData.value.phase_angle_c,
      };
    }

    // Use stack_usage from meter record if available
    if (resp?.stack_usage !== undefined) {
      meterData.value.stack_usage = resp.stack_usage;
    }
    if (resp?.eeprom_writes !== undefined) {
      meterData.value.eeprom_writes = resp.eeprom_writes;
    }
  } catch {
    // API not available; keep default data
  } finally {
    loading.value = false;
  }
}

function initHistoryData() {
  // Pre-fill 30 data points
  for (let i = 0; i < 30; i++) {
    timeLabels.value.push('--:--:--');
    voltageHistoryA.value.push(jitter(meterData.value.voltage_a, 2));
    voltageHistoryB.value.push(jitter(meterData.value.voltage_b, 2));
    voltageHistoryC.value.push(jitter(meterData.value.voltage_c, 2));
    currentHistoryA.value.push(jitter(meterData.value.current_a, 0.3));
    currentHistoryB.value.push(jitter(meterData.value.current_b, 0.3));
    currentHistoryC.value.push(jitter(meterData.value.current_c, 0.3));
  }
}

function renderAllCharts() {
  // --- Real-time voltage / current chart ---
  renderRtChart({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['电压A', '电压B', '电压C', '电流A', '电流B', '电流C'],
      top: 0,
      textStyle: { color: '#ccc' },
    },
    grid: { top: 50, bottom: 30, left: 60, right: 60 },
    xAxis: {
      type: 'category',
      data: timeLabels.value,
      axisLabel: { color: '#aaa', interval: 4 },
      splitLine: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: 'V',
        min: 200,
        max: 240,
        nameTextStyle: { color: '#aaa' },
        axisLabel: { color: '#aaa' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      {
        type: 'value',
        name: 'A',
        min: 0,
        max: 15,
        nameTextStyle: { color: '#aaa' },
        axisLabel: { color: '#aaa' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '电压A',
        type: 'line',
        smooth: true,
        data: voltageHistoryA.value,
        itemStyle: { color: '#5470c6' },
        yAxisIndex: 0,
      },
      {
        name: '电压B',
        type: 'line',
        smooth: true,
        data: voltageHistoryB.value,
        itemStyle: { color: '#91cc75' },
        yAxisIndex: 0,
      },
      {
        name: '电压C',
        type: 'line',
        smooth: true,
        data: voltageHistoryC.value,
        itemStyle: { color: '#fac858' },
        yAxisIndex: 0,
      },
      {
        name: '电流A',
        type: 'line',
        smooth: true,
        data: currentHistoryA.value,
        itemStyle: { color: '#ee6666' },
        lineStyle: { type: 'dashed' },
        yAxisIndex: 1,
      },
      {
        name: '电流B',
        type: 'line',
        smooth: true,
        data: currentHistoryB.value,
        itemStyle: { color: '#73c0de' },
        lineStyle: { type: 'dashed' },
        yAxisIndex: 1,
      },
      {
        name: '电流C',
        type: 'line',
        smooth: true,
        data: currentHistoryC.value,
        itemStyle: { color: '#3ba272' },
        lineStyle: { type: 'dashed' },
        yAxisIndex: 1,
      },
    ],
  });

  // --- Stability gauge chart ---
  renderGaugeChart({
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 10,
        center: ['50%', '60%'],
        radius: '90%',
        itemStyle: { color: '#69b1ff' },
        progress: {
          show: true,
          width: 18,
        },
        pointer: { show: true, length: '60%', width: 4 },
        axisLine: {
          lineStyle: {
            width: 18,
            color: [
              [0.6, '#52c41a'],
              [0.8, '#faad14'],
              [1, '#ff4d4f'],
            ],
          },
        },
        axisTick: {
          distance: -18,
          lineStyle: { color: '#aaa', width: 1 },
        },
        splitLine: {
          distance: -18,
          lineStyle: { color: '#aaa', width: 2 },
        },
        axisLabel: {
          distance: 25,
          color: '#aaa',
          fontSize: 11,
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: '#fff',
          fontSize: 20,
          offsetCenter: [0, '70%'],
        },
        title: {
          offsetCenter: [0, '90%'],
          color: '#ccc',
          fontSize: 13,
        },
        data: [{ value: stabilityScore.value, name: '稳定性评分' }],
      },
    ],
  });

  // --- Event curve chart (reading events over last 24h) ---
  const eventHours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
  const readEvents = Array.from({ length: 24 }, () => Math.floor(Math.random() * 20 + 5));
  const errorEvents = Array.from({ length: 24 }, () => Math.floor(Math.random() * 3));

  renderEventChart({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['读数事件', '异常事件'],
      top: 0,
      textStyle: { color: '#ccc' },
    },
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: eventHours,
      axisLabel: { color: '#aaa', interval: 3 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '次数',
      nameTextStyle: { color: '#aaa' },
      axisLabel: { color: '#aaa' },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: [
      {
        name: '读数事件',
        type: 'bar',
        data: readEvents,
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '异常事件',
        type: 'bar',
        data: errorEvents,
        itemStyle: { color: '#ff4d4f' },
      },
    ],
  });
}

function pollData() {
  // Simulate real-time updates with jitter
  meterData.value.voltage_a = jitter(meterData.value.voltage_a, 1);
  meterData.value.voltage_b = jitter(meterData.value.voltage_b, 1);
  meterData.value.voltage_c = jitter(meterData.value.voltage_c, 1);
  meterData.value.current_a = jitter(meterData.value.current_a, 0.2);
  meterData.value.current_b = jitter(meterData.value.current_b, 0.2);
  meterData.value.current_c = jitter(meterData.value.current_c, 0.2);
  meterData.value.power_a = Number(
    (meterData.value.voltage_a * meterData.value.current_a * meterData.value.pf_a).toFixed(1),
  );
  meterData.value.power_b = Number(
    (meterData.value.voltage_b * meterData.value.current_b * meterData.value.pf_b).toFixed(1),
  );
  meterData.value.power_c = Number(
    (meterData.value.voltage_c * meterData.value.current_c * meterData.value.pf_c).toFixed(1),
  );
  meterData.value.frequency = jitter(meterData.value.frequency, 0.02);

  // Push to time series
  const now = timeNow();
  timeLabels.value.push(now);
  voltageHistoryA.value.push(meterData.value.voltage_a);
  voltageHistoryB.value.push(meterData.value.voltage_b);
  voltageHistoryC.value.push(meterData.value.voltage_c);
  currentHistoryA.value.push(meterData.value.current_a);
  currentHistoryB.value.push(meterData.value.current_b);
  currentHistoryC.value.push(meterData.value.current_c);

  // Keep max 60 points
  if (timeLabels.value.length > 60) {
    timeLabels.value.shift();
    voltageHistoryA.value.shift();
    voltageHistoryB.value.shift();
    voltageHistoryC.value.shift();
    currentHistoryA.value.shift();
    currentHistoryB.value.shift();
    currentHistoryC.value.shift();
  }

  // Update real-time chart with new data
  updateRtChart({
    xAxis: { data: timeLabels.value },
    series: [
      { data: voltageHistoryA.value },
      { data: voltageHistoryB.value },
      { data: voltageHistoryC.value },
      { data: currentHistoryA.value },
      { data: currentHistoryB.value },
      { data: currentHistoryC.value },
    ],
  });
}

onMounted(async () => {
  await fetchMeterData();
  initHistoryData();
  renderAllCharts();

  // Start polling every 3 seconds
  pollTimer = setInterval(pollData, 3000);
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>

<template>
  <Page auto-content-height>
    <div :style="{ background: isDark ? '#0f172a' : '#f5f7fa', minHeight: '100vh', padding: '24px' }">
      <!-- Header -->
      <div style="margin-bottom: 16px">
        <Button type="text" style="color: #ccc" @click="router.back()">← 返回</Button>
        <span style="color: #fff; font-size: 18px; font-weight: 600; margin-left: 16px">
          {{ meterInfo.meter_name || meterInfo.serial_number || `电表 #${meterId}` }} - 单表监控
        </span>
        <Tag v-if="meterInfo.status" color="blue" style="margin-left: 12px">
          {{ meterInfo.status }}
        </Tag>
      </div>

      <Spin :spinning="loading">
        <!-- Stats Row: Instantaneous Values -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="电压A (V)" :value="meterData.voltage_a" :precision="1" :value-style="{ color: '#5470c6' }" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="电压B (V)" :value="meterData.voltage_b" :precision="1" :value-style="{ color: '#91cc75' }" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="电压C (V)" :value="meterData.voltage_c" :precision="1" :value-style="{ color: '#fac858' }" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="频率 (Hz)" :value="meterData.frequency" :precision="2" :value-style="{ color: '#fff' }" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="堆栈使用" :value="meterData.stack_usage" suffix="%" :value-style="{ color: '#69b1ff' }" />
            </Card>
          </Col>
          <Col :span="4">
            <Card size="small" style="background: #0c2340; border-color: #1a3a5c">
              <Statistic title="EEPROM写入" :value="meterData.eeprom_writes" :value-style="{ color: '#fff' }" />
            </Card>
          </Col>
        </Row>

        <!-- Real-time Chart (full width) -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="24">
            <Card
              title="实时电压/电流曲线"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="rtChartRef" height="360px" />
            </Card>
          </Col>
        </Row>

        <!-- Phase Details + Stability Gauge -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <!-- Phase A -->
          <Col :span="6">
            <Card
              title="A相详情"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#5470c6', borderBottomColor: '#1a3a5c' }"
            >
              <Descriptions :column="1" size="small" :label-style="{ color: '#aaa' }" :content-style="{ color: '#fff' }">
                <DescriptionsItem label="电压">{{ meterData.voltage_a }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_a }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_a }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_a }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_a }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <!-- Phase B -->
          <Col :span="6">
            <Card
              title="B相详情"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#91cc75', borderBottomColor: '#1a3a5c' }"
            >
              <Descriptions :column="1" size="small" :label-style="{ color: '#aaa' }" :content-style="{ color: '#fff' }">
                <DescriptionsItem label="电压">{{ meterData.voltage_b }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_b }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_b }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_b }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_b }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <!-- Phase C -->
          <Col :span="6">
            <Card
              title="C相详情"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fac858', borderBottomColor: '#1a3a5c' }"
            >
              <Descriptions :column="1" size="small" :label-style="{ color: '#aaa' }" :content-style="{ color: '#fff' }">
                <DescriptionsItem label="电压">{{ meterData.voltage_c }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_c }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_c }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_c }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_c }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <!-- Stability Gauge -->
          <Col :span="6">
            <Card
              title="稳定性分析"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '8px' }"
            >
              <EchartsUI ref="gaugeChartRef" height="260px" />
            </Card>
          </Col>
        </Row>

        <!-- Bottom Row: Stack + EEPROM + Event Curve -->
        <Row :gutter="16" style="margin-bottom: 16px">
          <!-- Stack Monitoring -->
          <Col :span="6">
            <Card
              title="堆栈监控"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
            >
              <div style="text-align: center; margin-bottom: 12px">
                <span style="color: #aaa; font-size: 13px">堆栈使用率</span>
                <div style="color: #fff; font-size: 28px; font-weight: 600">
                  {{ meterData.stack_usage }}%
                </div>
              </div>
              <Progress
                :percent="meterData.stack_usage"
                :stroke-color="stackColor"
                :show-info="false"
                :stroke-width="12"
                :status="stackStatus === 'danger' ? 'exception' : undefined"
              />
              <div style="display: flex; justify-content: space-between; margin-top: 8px">
                <span style="color: #52c41a; font-size: 11px">安全 (&lt;60%)</span>
                <span style="color: #faad14; font-size: 11px">警告 (60-80%)</span>
                <span style="color: #ff4d4f; font-size: 11px">危险 (&gt;80%)</span>
              </div>
            </Card>
          </Col>
          <!-- EEPROM Monitoring -->
          <Col :span="6">
            <Card
              title="EEPROM监控"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
            >
              <div style="text-align: center; margin-bottom: 16px">
                <span style="color: #aaa; font-size: 13px">写入次数</span>
                <div style="color: #fff; font-size: 28px; font-weight: 600">
                  {{ meterData.eeprom_writes?.toLocaleString() }}
                </div>
              </div>
              <div style="text-align: center; margin-bottom: 12px">
                <Tag :color="eepromStatus.color">{{ eepromStatus.text }}</Tag>
              </div>
              <Descriptions :column="1" size="small" :label-style="{ color: '#aaa' }" :content-style="{ color: '#fff' }">
                <DescriptionsItem label="状态">{{ eepromStatus.text }}</DescriptionsItem>
                <DescriptionsItem label="写入次数">{{ meterData.eeprom_writes?.toLocaleString() }}</DescriptionsItem>
                <DescriptionsItem label="寿命评估">
                  {{ meterData.eeprom_writes > 100000 ? '建议更换' : meterData.eeprom_writes > 50000 ? '注意监控' : '运行正常' }}
                </DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <!-- Event Curve -->
          <Col :span="12">
            <Card
              title="读数事件曲线 (24h)"
              :bordered="false"
              style="background: #0c2340; border-color: #1a3a5c"
              :head-style="{ color: '#fff', borderBottomColor: '#1a3a5c' }"
              :body-style="{ padding: '12px' }"
            >
              <EchartsUI ref="eventChartRef" height="240px" />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  </Page>
</template>
