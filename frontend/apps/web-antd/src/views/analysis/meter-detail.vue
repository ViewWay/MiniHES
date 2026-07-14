<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Row,
  Select,
  Spin,
  Table,
  Tabs,
  Tag,
} from 'ant-design-vue';

import { getDailyMeters, getMeterDetail } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const { watchThemeAndRerender } = useChartTheme();

// ── 状态 ──────────────────────────────────────────────────
const loading = ref(false);
const detailData = ref<any>(null);
const mode = ref<'pg' | 'direct'>('pg');

const allProjects = ref<any[]>([]);
const selectedProject = ref<number | undefined>();
const selectedMeter = ref<number | undefined>();
const meterOptions = ref<{ label: string; value: number }[]>([]);

const directDb = ref('');
const directCollection = ref('');

// ── 图表 refs ─────────────────────────────────────────────
const pqChartRef = ref<EchartsUIType>();
const voltageHistRef = ref<EchartsUIType>();
const lpChartRef = ref<EchartsUIType>();
const stackBarRef = ref<EchartsUIType>();
const stackTsRef = ref<EchartsUIType>();
const flashTsRef = ref<EchartsUIType>();
const eepromBarRef = ref<EchartsUIType>();
const eepromMaxRef = ref<EchartsUIType>();
const eepromTotalRef = ref<EchartsUIType>();

const { renderEcharts: renderPq } = useEcharts(pqChartRef);
const { renderEcharts: renderVoltageHist } = useEcharts(voltageHistRef);
const { renderEcharts: renderLp } = useEcharts(lpChartRef);
const { renderEcharts: renderStackBar } = useEcharts(stackBarRef);
const { renderEcharts: renderStackTs } = useEcharts(stackTsRef);
const { renderEcharts: renderFlashTs } = useEcharts(flashTsRef);
const { renderEcharts: renderEepromBar } = useEcharts(eepromBarRef);
const { renderEcharts: renderEepromMax } = useEcharts(eepromMaxRef);
const { renderEcharts: renderEepromTotal } = useEcharts(eepromTotalRef);

watchThemeAndRerender(renderAllCharts);

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#ff4d4f', '#13c2c2'];

// ── KPI ───────────────────────────────────────────────────
const kpiList = computed(() => {
  const d = detailData.value;
  if (!d) return [];
  const inst = d.instantaneous || {};
  const energy = d.energy || {};
  const isThree = d.phase_count === 3;
  const v1 = findInst(inst, 'voltage l1') || 0;
  const i1 = findInst(inst, 'current l1') || 0;
  const pImp = findInst(inst, 'active import power') || 0;
  const eImp = energy.cumulative_positive ?? 0;
  return [
    { label: isThree ? '三相电压均值' : '电压 L1', value: isThree ? avgThree(inst, 'voltage') : v1, unit: 'V', color: COLORS[0] },
    { label: isThree ? '三相电流总和' : '电流 L1', value: isThree ? sumThree(inst, 'current') : i1, unit: 'A', color: COLORS[1] },
    { label: '有功功率 (导入)', value: pImp, unit: 'W', color: COLORS[2] },
    { label: '累计正向有功电能', value: eImp, unit: 'kWh', color: COLORS[4] },
  ];
});

// ── 事件 Tab ──────────────────────────────────────────────
const activeEventTab = ref('all');
const eventTabs = computed(() => {
  const buckets = detailData.value?.events?.buckets || {};
  const labels: Record<string, string> = {
    standard: '标准事件', fraud: '防窃电', quality: '电能质量',
    communication: '通信', disconnector: '断路器', other: '其他',
  };
  return Object.entries(labels)
    .filter(([k]) => (buckets[k] || []).length > 0)
    .map(([k, label]) => ({ key: k, label: `${label} (${buckets[k].length})` }));
});
const eventColumns = [
  { title: '时间', dataIndex: 't', key: 't', width: 160 },
  { title: '事件码', dataIndex: 'code', key: 'code', width: 100 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
];
const currentEvents = computed(() => {
  const buckets = detailData.value?.events?.buckets || {};
  if (activeEventTab.value === 'all') {
    return Object.entries(buckets).flatMap(([type, items]) =>
      (items as any[]).map((it) => ({ ...it, type })),
    );
  }
  return (buckets[activeEventTab.value] || []).map((it: any) => ({ ...it, type: activeEventTab.value }));
});

// ── 辅助函数 ──────────────────────────────────────────────
function findInst(inst: any, keyword: string): number | undefined {
  for (const [k, v] of Object.entries(inst)) {
    if (k.toLowerCase().includes(keyword)) {
      const n = Number(v);
      return Number.isFinite(n) ? n : undefined;
    }
  }
  return undefined;
}

function avgThree(inst: any, keyword: string): number {
  const vals = ['l1', 'l2', 'l3']
    .map((ph) => findInst(inst, `${keyword} ${ph}`))
    .filter((v): v is number => v !== undefined);
  return vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10 : 0;
}

function sumThree(inst: any, keyword: string): number {
  return ['l1', 'l2', 'l3']
    .map((ph) => findInst(inst, `${keyword} ${ph}`) || 0)
    .reduce((a, b) => a + b, 0);
}

// ── 数据加载 ──────────────────────────────────────────────
async function fetchProjects() {
  try {
    const res = await getProjectList();
    allProjects.value = (res.items || res || []).filter((p: any) => p.mongo_database);
    if (allProjects.value.length > 0 && allProjects.value[0]) {
      selectedProject.value = allProjects.value[0].id;
    }
  } catch {
    // ignore
  }
}

async function fetchMeters(projectId?: number) {
  if (!projectId) return;
  try {
    const res = await getDailyMeters({ project_id: projectId });
    meterOptions.value = (res.items || []).map((m: any) => ({
      label: `${m.serial_number} - ${m.meter_name}`,
      value: m.id,
    }));
    if (meterOptions.value.length > 0 && meterOptions.value[0]) {
      selectedMeter.value = meterOptions.value[0].value;
    }
  } catch {
    // ignore
  }
}

async function handleSearch() {
  loading.value = true;
  detailData.value = null;
  try {
    let params: any;
    if (mode.value === 'pg') {
      if (!selectedMeter.value) return;
      params = { meter_id: selectedMeter.value, days: 60 };
    } else {
      if (!directDb.value || !directCollection.value) return;
      params = { db: directDb.value, collection: directCollection.value, days: 60 };
    }
    const res = await getMeterDetail(params);
    detailData.value = res;
    setTimeout(() => renderAllCharts(), 100);
  } catch (e: any) {
    console.error('meter-detail load failed', e);
  } finally {
    loading.value = false;
  }
}

watch(selectedProject, (val) => {
  if (val && mode.value === 'pg') fetchMeters(val);
});

// ── 图表渲染 ──────────────────────────────────────────────
function renderAllCharts() {
  if (!detailData.value) return;
  renderPqChart();
  renderVoltageHistChart();
  renderLpChart();
  renderStackBarChart();
  renderStackTsChart();
  renderFlashTsChart();
  renderEepromBarChart();
  renderEepromMaxChart();
  renderEepromTotalChart();
}

const NAME_STYLE = { nameGap: 15, nameTextStyle: { color: '#888', fontSize: 11 } };

function renderPqChart() {
  const pq = detailData.value?.power_quality?.points || [];
  if (pq.length === 0) return;
  renderPq({
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 }, data: ['Vmin', 'Vmax', 'Vavg'] },
    grid: { left: 50, right: 20, top: 35, bottom: 45 },
    xAxis: { type: 'category', data: pq.map((p: any) => p.t.slice(5)), axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: 'V', min: 180, max: 260, ...NAME_STYLE },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 5 }],
    series: [
      { name: 'Vmin', type: 'line', smooth: true, showSymbol: false, data: pq.map((p: any) => p.vmin), lineStyle: { color: '#ff4d4f', width: 1.5 }, itemStyle: { color: '#ff4d4f' } },
      { name: 'Vmax', type: 'line', smooth: true, showSymbol: false, data: pq.map((p: any) => p.vmax), lineStyle: { color: '#722ed1', width: 1.5 }, itemStyle: { color: '#722ed1' } },
      {
        name: 'Vavg', type: 'line', smooth: true, showSymbol: false, data: pq.map((p: any) => p.vavg),
        lineStyle: { color: '#1890ff', width: 2 }, itemStyle: { color: '#1890ff' },
        markLine: { data: [{ yAxis: 198, name: 'sag', lineStyle: { color: '#ff4d4f', type: 'dashed' } }, { yAxis: 242, name: 'swell', lineStyle: { color: '#722ed1', type: 'dashed' } }] },
      },
    ],
  });
}

function renderVoltageHistChart() {
  const pq = detailData.value?.power_quality?.points || [];
  const vavgs = pq.map((p: any) => p.vavg).filter((v: number) => v > 0);
  const labels: string[] = [];
  const bins: number[] = [];
  for (let v = 180; v <= 240; v += 5) {
    labels.push(`${v}-${v + 5}`);
    bins.push(0);
  }
  vavgs.forEach((v: number) => {
    const i = Math.min(12, Math.floor((v - 180) / 5));
    if (i >= 0) bins[i] = (bins[i] || 0) + 1;
  });
  renderVoltageHist({
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 25, bottom: 40 },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: '次数', ...NAME_STYLE },
    series: [{
      type: 'bar', data: bins, barWidth: '70%',
      itemStyle: { color: (p: any) => { const v = 180 + p.dataIndex * 5; if (v < 198) return '#ff4d4f'; if (v > 240) return '#722ed1'; return '#52c41a'; } },
    }],
  });
}

function renderLpChart() {
  const lp = detailData.value?.load_profile || [];
  if (lp.length === 0) return;
  renderLp({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 30, bottom: 45 },
    xAxis: { type: 'category', data: lp.map((p: any) => p.time_slot || p.raw_timestamp?.slice(11) || ''), axisLabel: { fontSize: 9 } },
    yAxis: { type: 'value', name: '累计电能', ...NAME_STYLE },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 5 }],
    series: [{ type: 'line', smooth: true, showSymbol: false, data: lp.map((p: any) => p.cumulative_energy), areaStyle: { color: 'rgba(24,144,255,.15)' }, lineStyle: { color: '#1890ff', width: 2 }, itemStyle: { color: '#1890ff' } }],
  });
}

function renderStackBarChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  if (tl.length === 0) return;
  const last = tl.at(-1);
  const segs = last?.stack?.segments || {};
  const names = Object.keys(segs);
  renderStackBar({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 70, right: 20, top: 25, bottom: 40 },
    xAxis: { type: 'value', name: 'bytes', ...NAME_STYLE },
    yAxis: { type: 'category', data: names },
    series: [
      { name: '已用', type: 'bar', data: names.map((n) => segs[n].used), itemStyle: { color: '#52c41a', borderRadius: [0, 4, 4, 0] } },
      { name: '总量', type: 'bar', data: names.map((n) => segs[n].size), itemStyle: { color: '#e8e8e8', borderRadius: [0, 4, 4, 0] } },
    ],
  });
}

function renderStackTsChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  if (tl.length === 0) return;
  const segNames = new Set<string>();
  tl.forEach((p: any) => Object.keys(p.stack?.segments || {}).forEach((n) => segNames.add(n)));
  const names = [...segNames];
  renderStackTs({
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 }, data: names },
    grid: { left: 60, right: 20, top: 25, bottom: 50 },
    xAxis: { type: 'category', data: tl.map((p: any) => p.t.slice(5, 16)), axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: 'used (bytes)', ...NAME_STYLE },
    series: names.map((n, i) => ({
      name: n, type: 'line', smooth: true, showSymbol: false,
      data: tl.map((p: any) => p.stack?.segments?.[n]?.used ?? 0),
      lineStyle: { color: COLORS[i % COLORS.length] }, itemStyle: { color: COLORS[i % COLORS.length] },
    })),
  });
}

function renderFlashTsChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  if (tl.length === 0) return;
  const sectorSet = new Set<string>();
  tl.forEach((p: any) => Object.keys(p.flash || {}).forEach((s) => sectorSet.add(s)));
  const sids = [...sectorSet].sort();
  renderFlashTs({
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 10 }, data: sids.map((s) => `0x${s}`), type: 'scroll' },
    grid: { left: 60, right: 20, top: 25, bottom: 50 },
    xAxis: { type: 'category', data: tl.map((p: any) => p.t.slice(5, 16)), axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: '擦写次数', ...NAME_STYLE },
    series: sids.map((s, i) => ({
      name: `0x${s}`, type: 'line', smooth: true, showSymbol: false,
      data: tl.map((p: any) => p.flash?.[s] ?? 0),
      lineStyle: { color: COLORS[i % COLORS.length] }, itemStyle: { color: COLORS[i % COLORS.length] },
    })),
  });
}

function renderEepromBarChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  if (tl.length === 0) return;
  const last = tl.at(-1);
  const top = last?.eeprom?.top || [];
  const maxVal = last?.eeprom?.max || 1;
  renderEepromBar({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 50, right: 20, top: 25, bottom: 40 },
    xAxis: { type: 'category', data: top.map((t: any) => `#${t.idx}`), axisLabel: { fontSize: 9, rotate: 30 } },
    yAxis: { type: 'value', name: '擦写次数', ...NAME_STYLE },
    series: [{
      type: 'bar', data: top.map((t: any) => t.val),
      itemStyle: { borderRadius: [4, 4, 0, 0], color: (p: any) => { const v = p.value; if (v > maxVal * 0.8) return '#ff4d4f'; if (v > maxVal * 0.5) return '#faad14'; return '#52c41a'; } },
    }],
  });
}

function renderEepromMaxChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  renderEepromMax({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 25, bottom: 50 },
    xAxis: { type: 'category', data: tl.map((p: any) => p.t.slice(5, 16)), axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: '最高擦写', ...NAME_STYLE },
    series: [{ type: 'line', smooth: true, data: tl.map((p: any) => p.eeprom?.max ?? 0), areaStyle: { color: 'rgba(255,77,79,.15)' }, lineStyle: { color: '#ff4d4f', width: 2 } }],
  });
}

function renderEepromTotalChart() {
  const tl = detailData.value?.hardware?.timeline || [];
  renderEepromTotal({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 25, bottom: 50 },
    xAxis: { type: 'category', data: tl.map((p: any) => p.t.slice(5, 16)), axisLabel: { rotate: 30, fontSize: 9 } },
    yAxis: { type: 'value', name: '累计擦写', ...NAME_STYLE },
    series: [{ type: 'line', smooth: true, data: tl.map((p: any) => p.eeprom?.total ?? 0), areaStyle: { color: 'rgba(250,173,20,.15)' }, lineStyle: { color: '#faad14', width: 2 } }],
  });
}

onMounted(() => {
  fetchProjects();
});
</script>

<template>
  <Page auto-content-height>
    <!-- 筛选区 -->
    <Card style="margin-bottom: 12px">
      <Tabs v-model:active-key="mode" size="small">
        <Tabs.TabPane key="pg" tab="按电表选择" />
        <Tabs.TabPane key="direct" tab="直接输入 Mongo" />
      </Tabs>
      <Form layout="inline" style="margin-top: 8px">
        <template v-if="mode === 'pg'">
          <Form.Item label="项目">
            <Select
              v-model:value="selectedProject"
              placeholder="选择项目"
              style="width: 260px"
              :options="allProjects.map((p) => ({ label: p.name, value: p.id }))"
              show-search
              option-filter-prop="label"
            />
          </Form.Item>
          <Form.Item label="电表">
            <Select
              v-model:value="selectedMeter"
              placeholder="选择电表"
              style="width: 280px"
              :options="meterOptions"
              show-search
              option-filter-prop="label"
            />
          </Form.Item>
        </template>
        <template v-else>
          <Form.Item label="Mongo 库">
            <Input v-model:value="directDb" placeholder="如 Leopard-08_LVCT_DailyCheck" style="width: 260px" />
          </Form.Item>
          <Form.Item label="集合">
            <Input v-model:value="directCollection" placeholder="如 KFM0600260520012" style="width: 240px" />
          </Form.Item>
        </template>
        <Form.Item>
          <Button type="primary" :loading="loading" @click="handleSearch">查询</Button>
        </Form.Item>
      </Form>
    </Card>

    <Spin :spinning="loading">
      <template v-if="detailData">
        <Alert
          v-if="detailData.warning"
          :message="detailData.warning"
          type="warning"
          show-icon
          style="margin-bottom: 12px"
        />

        <!-- 设备信息 + KPI -->
        <Card style="margin-bottom: 12px">
          <Row :gutter="16">
            <Col v-for="kpi in kpiList" :key="kpi.label" :xs="12" :sm="6">
              <Card size="small" :bordered="false" style="text-align: center; background: #fafafa">
                <div style="font-size: 12px; color: #888">{{ kpi.label }}</div>
                <div style="font-size: 24px; font-weight: 700; color: #333">
                  {{ kpi.value }}<span style="font-size: 13px; color: #999; margin-left: 3px">{{ kpi.unit }}</span>
                </div>
              </Card>
            </Col>
          </Row>
          <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: #666; margin-top: 12px">
            <span>设备 ID: <strong>{{ detailData.device_meta?.device_id || '—' }}</strong></span>
            <span>逻辑名: {{ detailData.device_meta?.logical_name || '—' }}</span>
            <span>表型: <Tag :color="detailData.meter_type === 'three' ? 'blue' : 'orange'">{{ detailData.meter_type === 'three' ? '三相' : '单相' }}</Tag></span>
            <span>固件: APP1={{ detailData.connection?.app1_version || '?' }} / APP2={{ detailData.connection?.app2_version || '?' }}</span>
            <span>时钟: {{ detailData.device_meta?.clock_time || '—' }}</span>
            <span>Mongo: <code>{{ detailData.mongo_db }}.{{ detailData.mongo_collection }}</code></span>
          </div>
        </Card>

        <!-- PQ 电压质量 -->
        <Card title="⚡ Power Quality 电压质量曲线（sag / swell）" size="small" style="margin-bottom: 12px">
          <template #extra>
            <Tag color="red">Sag: {{ detailData.power_quality.sag_count }}</Tag>
            <Tag color="purple">Swell: {{ detailData.power_quality.swell_count }}</Tag>
            <Tag color="green">合格率: {{ detailData.power_quality.pass_rate }}%</Tag>
          </template>
          <EchartsUI v-if="detailData.power_quality.total > 0" ref="pqChartRef" height="340px" />
          <Empty v-else description="该电表无 Power Quality Profile 数据" />
        </Card>

        <Row v-if="detailData.power_quality.total > 0" :gutter="12" style="margin-bottom: 12px">
          <Col :xs="24" :sm="12">
            <Card title="电压分布直方图" size="small">
              <EchartsUI ref="voltageHistRef" height="240px" />
            </Card>
          </Col>
          <Col :xs="24" :sm="12">
            <Card size="small">
              <template #title>瞬时值明细</template>
              <div style="font-size: 12px; line-height: 2; max-height: 240px; overflow-y: auto">
                <div v-for="(v, k) in detailData.instantaneous" :key="k" style="display: flex; justify-content: space-between; border-bottom: 1px solid #f5f5f5">
                  <span style="color: #888">{{ k }}</span>
                  <strong>{{ v }}</strong>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        <!-- 负荷曲线 -->
        <Card title="负荷曲线 (Load Profile)" size="small" style="margin-bottom: 12px">
          <template #extra><Tag>{{ detailData.load_profile.length }} 点</Tag></template>
          <EchartsUI v-if="detailData.load_profile.length > 0" ref="lpChartRef" height="300px" />
          <Empty v-else description="无负荷曲线数据" />
        </Card>

        <!-- 硬件状态 -->
        <Card title="🖥 嵌入式硬件状态" size="small" style="margin-bottom: 12px">
          <template #extra><Tag color="green">{{ detailData.hardware.count }} 个采样点</Tag></template>
          <Row v-if="detailData.hardware.count > 0" :gutter="12">
            <Col :xs="24" :sm="12">
              <Card title="各栈段使用率" size="small" :bordered="false">
                <EchartsUI ref="stackBarRef" height="240px" />
              </Card>
            </Col>
            <Col :xs="24" :sm="12">
              <Card title="栈使用量趋势" size="small" :bordered="false">
                <EchartsUI ref="stackTsRef" height="240px" />
              </Card>
            </Col>
            <Col :span="24" style="margin-top: 12px">
              <Card title="Flash 擦写趋势" size="small" :bordered="false">
                <EchartsUI ref="flashTsRef" height="240px" />
              </Card>
            </Col>
            <Col :xs="24" :sm="8" style="margin-top: 12px">
              <Card title="EEPROM Top 扇区" size="small" :bordered="false">
                <EchartsUI ref="eepromBarRef" height="240px" />
              </Card>
            </Col>
            <Col :xs="24" :sm="8" style="margin-top: 12px">
              <Card title="EEPROM 最高擦写" size="small" :bordered="false">
                <EchartsUI ref="eepromMaxRef" height="240px" />
              </Card>
            </Col>
            <Col :xs="24" :sm="8" style="margin-top: 12px">
              <Card title="EEPROM 累计擦写" size="small" :bordered="false">
                <EchartsUI ref="eepromTotalRef" height="240px" />
              </Card>
            </Col>
          </Row>
          <Empty v-else description="无硬件状态数据" />
        </Card>

        <!-- 事件日志 -->
        <Card title="事件日志" size="small">
          <Tabs v-model:active-key="activeEventTab">
            <Tabs.TabPane key="all" :tab="`全部 (${Object.values(detailData.events.summary).reduce((a: number, b: any) => a + (b || 0), 0)})`" />
            <Tabs.TabPane v-for="tab in eventTabs" :key="tab.key" :tab="tab.label" />
          </Tabs>
          <Table
            :columns="eventColumns"
            :data-source="currentEvents"
            :pagination="{ pageSize: 20, size: 'small' }"
            size="small"
            :scroll="{ y: 400 }"
            row-key="t"
          />
        </Card>
      </template>

      <Empty v-else-if="!loading" description="选择电表后点击查询" style="padding: 60px" />
    </Spin>
  </Page>
</template>
