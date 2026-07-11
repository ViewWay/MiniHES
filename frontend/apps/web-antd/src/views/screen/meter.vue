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

const { chartColors, themedAxis, themedTooltip, themedLegend, themedGauge, watchThemeAndRerender } = useChartTheme();
const route = useRoute();
const router = useRouter();
const meterId = ref(Number(route.params.id) || 0);

const loading = ref(true);
const meterInfo = ref<Record<string, any>>({});

const meterData = ref({
  voltage_a: 0,
  voltage_b: 0,
  voltage_c: 0,
  current_a: 0,
  current_b: 0,
  current_c: 0,
  power_a: 0,
  power_b: 0,
  power_c: 0,
  pf_a: 0,
  pf_b: 0,
  pf_c: 0,
  frequency: 0,
  stack_usage: 0,
  eeprom_writes: 0,
  phase_angle_a: 0,
  phase_angle_b: 0,
  phase_angle_c: 0,
});

const stabilityScore = ref(0);

const timeLabels = ref<string[]>([]);
const voltageHistoryA = ref<number[]>([]);
const voltageHistoryB = ref<number[]>([]);
const voltageHistoryC = ref<number[]>([]);
const currentHistoryA = ref<number[]>([]);
const currentHistoryB = ref<number[]>([]);
const currentHistoryC = ref<number[]>([]);

let pollTimer: ReturnType<typeof setInterval> | null = null;

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

async function fetchMeterData() {
  loading.value = true;
  try {
    const resp = await getMeterDetail(meterId.value);
    meterInfo.value = resp;

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
  timeLabels.value = [];
  voltageHistoryA.value = [];
  voltageHistoryB.value = [];
  voltageHistoryC.value = [];
  currentHistoryA.value = [];
  currentHistoryB.value = [];
  currentHistoryC.value = [];
}

function renderAllCharts() {
  const c = chartColors.value;
  const gauge = themedGauge();

  renderRtChart({
    tooltip: themedTooltip(),
    legend: themedLegend({
      data: ['电压A', '电压B', '电压C', '电流A', '电流B', '电流C'],
      top: 0,
    }),
    grid: { top: 50, bottom: 30, left: 60, right: 60 },
    xAxis: themedAxis('x', {
      type: 'category',
      data: timeLabels.value,
      axisLabel: { color: c.text, interval: 4 },
    }),
    yAxis: [
      themedAxis('y', { type: 'value', name: 'V', min: 200, max: 240 }),
      themedAxis('y', { type: 'value', name: 'A', min: 0, max: 15, splitLine: { show: false } }),
    ],
    series: [
      { name: '电压A', type: 'line', smooth: true, data: voltageHistoryA.value, itemStyle: { color: '#5470c6' }, yAxisIndex: 0 },
      { name: '电压B', type: 'line', smooth: true, data: voltageHistoryB.value, itemStyle: { color: '#91cc75' }, yAxisIndex: 0 },
      { name: '电压C', type: 'line', smooth: true, data: voltageHistoryC.value, itemStyle: { color: '#fac858' }, yAxisIndex: 0 },
      { name: '电流A', type: 'line', smooth: true, data: currentHistoryA.value, itemStyle: { color: '#ee6666' }, lineStyle: { type: 'dashed' }, yAxisIndex: 1 },
      { name: '电流B', type: 'line', smooth: true, data: currentHistoryB.value, itemStyle: { color: '#73c0de' }, lineStyle: { type: 'dashed' }, yAxisIndex: 1 },
      { name: '电流C', type: 'line', smooth: true, data: currentHistoryC.value, itemStyle: { color: '#3ba272' }, lineStyle: { type: 'dashed' }, yAxisIndex: 1 },
    ],
  });

  renderGaugeChart({
    series: [{
      type: 'gauge',
      startAngle: 200, endAngle: -20,
      min: 0, max: 100, splitNumber: 10,
      center: ['50%', '60%'], radius: '90%',
      itemStyle: { color: '#69b1ff' },
      progress: { show: true, width: 18 },
      pointer: { show: true, length: '60%', width: 4 },
      axisLine: {
        lineStyle: {
          width: 18,
          color: [[0.6, '#52c41a'], [0.8, '#faad14'], [1, '#ff4d4f']],
        },
      },
      axisTick: gauge.axisTick,
      splitLine: gauge.splitLine,
      axisLabel: gauge.axisLabel,
      detail: { valueAnimation: true, formatter: '{value}%', color: gauge.detail.color, fontSize: 20, offsetCenter: [0, '70%'] },
      title: { offsetCenter: [0, '90%'], color: gauge.title.color, fontSize: 13 },
      data: [{ value: stabilityScore.value, name: '稳定性评分' }],
    }],
  });

  const eventHours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
  const readEvents: number[] = [];
  const errorEvents: number[] = [];

  renderEventChart({
    tooltip: themedTooltip(),
    legend: themedLegend({ data: ['读数事件', '异常事件'], top: 0 }),
    grid: { top: 40, bottom: 30, left: 50, right: 20 },
    xAxis: themedAxis('x', { type: 'category', data: eventHours, axisLabel: { color: c.text, interval: 3 } }),
    yAxis: themedAxis('y', { type: 'value', name: '次数' }),
    series: [
      { name: '读数事件', type: 'bar', data: readEvents, itemStyle: { color: '#1890ff' } },
      { name: '异常事件', type: 'bar', data: errorEvents, itemStyle: { color: '#ff4d4f' } },
    ],
  });
}

async function pollData() {
  // Only update from API response; do not generate fake data.
  try {
    const resp = await getMeterDetail(meterId.value);
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

      const now = timeNow();
      timeLabels.value.push(now);
      voltageHistoryA.value.push(meterData.value.voltage_a);
      voltageHistoryB.value.push(meterData.value.voltage_b);
      voltageHistoryC.value.push(meterData.value.voltage_c);
      currentHistoryA.value.push(meterData.value.current_a);
      currentHistoryB.value.push(meterData.value.current_b);
      currentHistoryC.value.push(meterData.value.current_c);

      if (timeLabels.value.length > 60) {
        timeLabels.value.shift();
        voltageHistoryA.value.shift();
        voltageHistoryB.value.shift();
        voltageHistoryC.value.shift();
        currentHistoryA.value.shift();
        currentHistoryB.value.shift();
        currentHistoryC.value.shift();
      }

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
    if (resp?.stack_usage !== undefined) {
      meterData.value.stack_usage = resp.stack_usage;
    }
    if (resp?.eeprom_writes !== undefined) {
      meterData.value.eeprom_writes = resp.eeprom_writes;
    }
  } catch {
    // API not available; keep current data, do not mutate randomly
  }
}

onMounted(async () => {
  await fetchMeterData();
  initHistoryData();
  renderAllCharts();
  watchThemeAndRerender(renderAllCharts);
  pollTimer = setInterval(() => {
    void pollData().catch((err) => console.error('[meter] pollData failed', err));
  }, 3000);
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
      <div style="margin-bottom: 16px; display: flex; align-items: center">
        <Button type="link" @click="router.back()">← 返回</Button>
        <span style="font-size: 16px; font-weight: 600; margin-left: 8px">
          {{ meterInfo.meter_name || meterInfo.serial_number || `电表 #${meterId}` }} - 单表监控
        </span>
        <Tag v-if="meterInfo.status" color="blue" style="margin-left: 12px">
          {{ meterInfo.status }}
        </Tag>
      </div>

      <Spin :spinning="loading">
        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="电压A (V)" :value="meterData.voltage_a" :precision="1" :value-style="{ color: '#5470c6' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="电压B (V)" :value="meterData.voltage_b" :precision="1" :value-style="{ color: '#91cc75' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="电压C (V)" :value="meterData.voltage_c" :precision="1" :value-style="{ color: '#fac858' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="频率 (Hz)" :value="meterData.frequency" :precision="2" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="堆栈使用" :value="meterData.stack_usage" suffix="%" :value-style="{ color: '#69b1ff' }" />
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <Statistic title="EEPROM写入" :value="meterData.eeprom_writes" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="24">
            <Card title="实时电压/电流曲线" :bordered="false">
              <EchartsUI ref="rtChartRef" height="300px" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6">
            <Card title="A相详情" :bordered="false">
              <template #title><span style="color: #5470c6">A相详情</span></template>
              <Descriptions :column="1" size="small">
                <DescriptionsItem label="电压">{{ meterData.voltage_a }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_a }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_a }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_a }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_a }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <template #title><span style="color: #91cc75">B相详情</span></template>
              <Descriptions :column="1" size="small">
                <DescriptionsItem label="电压">{{ meterData.voltage_b }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_b }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_b }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_b }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_b }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <Col :span="6">
            <Card :bordered="false">
              <template #title><span style="color: #fac858">C相详情</span></template>
              <Descriptions :column="1" size="small">
                <DescriptionsItem label="电压">{{ meterData.voltage_c }} V</DescriptionsItem>
                <DescriptionsItem label="电流">{{ meterData.current_c }} A</DescriptionsItem>
                <DescriptionsItem label="功率">{{ meterData.power_c }} W</DescriptionsItem>
                <DescriptionsItem label="功率因数">{{ meterData.pf_c }}</DescriptionsItem>
                <DescriptionsItem label="相位角">{{ meterData.phase_angle_c }}&deg;</DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <Col :span="6">
            <Card title="稳定性分析" :bordered="false">
              <EchartsUI ref="gaugeChartRef" height="300px" />
            </Card>
          </Col>
        </Row>

        <Row :gutter="16" style="margin-bottom: 16px">
          <Col :span="6">
            <Card title="堆栈监控" :bordered="false">
              <div style="text-align: center; margin-bottom: 12px">
                <div style="font-size: 13px; opacity: 0.65">堆栈使用率</div>
                <div style="font-size: 28px; font-weight: 600">
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
          <Col :span="6">
            <Card title="EEPROM监控" :bordered="false">
              <div style="text-align: center; margin-bottom: 16px">
                <div style="font-size: 13px; opacity: 0.65">写入次数</div>
                <div style="font-size: 28px; font-weight: 600">
                  {{ meterData.eeprom_writes?.toLocaleString() }}
                </div>
              </div>
              <div style="text-align: center; margin-bottom: 12px">
                <Tag :color="eepromStatus.color">{{ eepromStatus.text }}</Tag>
              </div>
              <Descriptions :column="1" size="small">
                <DescriptionsItem label="状态">{{ eepromStatus.text }}</DescriptionsItem>
                <DescriptionsItem label="写入次数">{{ meterData.eeprom_writes?.toLocaleString() }}</DescriptionsItem>
                <DescriptionsItem label="寿命评估">
                  {{ meterData.eeprom_writes > 100000 ? '建议更换' : meterData.eeprom_writes > 50000 ? '注意监控' : '运行正常' }}
                </DescriptionsItem>
              </Descriptions>
            </Card>
          </Col>
          <Col :span="12">
            <Card title="读数事件曲线 (24h)" :bordered="false">
              <EchartsUI ref="eventChartRef" height="300px" />
            </Card>
          </Col>
        </Row>
      </Spin>
  </Page>
</template>
