<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Badge,
  Card,
  Col,
  Progress,
  Row,
  Spin,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getProjectList } from '#/api/modules/project';
import { getMeterList } from '#/api/modules/meter';
import { useChartTheme } from '#/composables/useChartTheme';
import { THEME_COLORS } from '#/constants';

const router = useRouter();
const { isDark, chartColors, themedAxis, themedTooltip, themedLegend } = useChartTheme();

const pageVars = computed(() => {
  const dark = isDark.value;
  return {
    '--bg': dark ? '#0f172a' : '#f5f7fa',
    '--bg-card': dark ? '#1e293b' : '#ffffff',
    '--border': dark ? '#334155' : '#e2e8f0',
    '--text': dark ? '#f1f5f9' : '#1e293b',
    '--text-sec': dark ? '#94a3b8' : '#64748b',
    '--text-muted': dark ? '#cccccc' : '#6b7280',
  };
});

const loading = ref(false);
const projects = ref<any[]>([]);
const totalMeters = ref(0);
const onlineMeters = ref(0);
const offlineMeters = ref(0);
const alertCount = ref(0);
const onlineRate = ref(0);

const eventStats = ref([
  { type: '标准事件', count: 0, color: '#1890ff' },
  { type: '窃电事件', count: 0, color: '#ff4d4f' },
  { type: '通信事件', count: 0, color: '#fa8c16' },
  { type: '预付费事件', count: 0, color: '#13c2c2' },
]);

const stackChartRef = ref<EchartsUIType>();
const { renderEcharts: renderStackChart } = useEcharts(stackChartRef);

const onlineRateChartRef = ref<EchartsUIType>();
const { renderEcharts: renderOnlineRateChart } = useEcharts(onlineRateChartRef);

const alarmTrendChartRef = ref<EchartsUIType>();
const { renderEcharts: renderAlarmTrendChart } = useEcharts(alarmTrendChartRef);

const columns = [
  { title: '项目名称', dataIndex: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '设备/在线', key: 'online', width: 100 },
  { title: '告警', dataIndex: 'alert_count', key: 'alert_count', width: 60 },
  { title: '测试进度', key: 'progress', width: 160 },
  { title: '测试天数', dataIndex: 'days', width: 80 },
  { title: '测试负责人', dataIndex: 'test_leader', width: 100 },
  { title: '操作', key: 'action', width: 100 },
];

function goToProject(id: number) {
  router.push({ path: '/screen/project', query: { id } });
}

function renderAllCharts() {
  renderStackChart(buildStackOptions());
  renderOnlineRateChart(buildOnlineRateOptions());
  renderAlarmTrendChart(buildAlarmTrendOptions());
}

onMounted(async () => {
  loading.value = true;
  try {
    const projectRes = await getProjectList({ page: 1 });
    const projectList = projectRes?.items || projectRes?.data || projectRes || [];
    projects.value = Array.isArray(projectList) ? projectList : [];

    const meterRes = await getMeterList({ page: 1, page_size: 1000 });
    const meterList = meterRes?.items || meterRes?.data || [];

    totalMeters.value = Array.isArray(meterList) ? meterList.length : (meterRes?.total || 0);
    onlineMeters.value = Array.isArray(meterList) ? meterList.filter((m: any) => m.online_status === 'online').length : (meterRes?.online_count || 0);
    offlineMeters.value = totalMeters.value - onlineMeters.value;
    alertCount.value = Array.isArray(meterList) ? meterList.filter((m: any) => m.alert_count && m.alert_count > 0).length : 0;
    onlineRate.value = totalMeters.value > 0 ? Number(((onlineMeters.value / totalMeters.value) * 100).toFixed(1)) : 0;
  } catch {
    // fallback
  } finally {
    loading.value = false;
  }

  renderAllCharts();
});

watch(isDark, () => renderAllCharts());

function buildStackOptions(): any {
  const c = chartColors.value;
  const categories = ['协议栈', '采集引擎', '数据解析', '任务队列', '通信缓冲'];
  const used = [72, 58, 45, 63, 38];
  const remaining = used.map((v) => 100 - v);

  return {
    title: { text: '堆栈使用率分布', textStyle: { color: c.text, fontSize: 14 }, left: 'center' },
    tooltip: themedTooltip({ axisPointer: { type: 'shadow' } }),
    legend: themedLegend({ data: ['已使用', '剩余'], bottom: 0 }),
    grid: { top: 40, left: '3%', right: '4%', bottom: 40, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: categories }),
    yAxis: themedAxis('y', { type: 'value', name: '使用率 (%)' }),
    series: [
      {
        name: '已使用', type: 'bar', stack: 'total', barWidth: '50%',
        data: used.map((v) => ({
          value: v,
          itemStyle: { color: v >= 80 ? '#ff4d4f' : v >= 60 ? '#faad14' : '#52c41a' },
        })),
        label: { show: true, position: 'inside', formatter: '{c}%', color: '#fff', fontSize: 11 },
      },
      {
        name: '剩余', type: 'bar', stack: 'total',
        data: remaining,
        itemStyle: { color: isDark.value ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)' },
        label: { show: false },
      },
    ],
  };
}

function buildOnlineRateOptions(): any {
  const c = chartColors.value;
  return {
    title: {
      text: '在线率', subtext: `${onlineRate.value}%`,
      left: 'center', top: 'center',
      textStyle: { color: c.text, fontSize: 14, lineHeight: 20 },
      subtextStyle: { color: onlineRate.value >= 95 ? '#52c41a' : '#faad14', fontSize: 24, fontWeight: 'bold' },
    },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['55%', '80%'], center: ['50%', '50%'],
      avoidLabelOverlap: false, label: { show: false }, emphasis: { label: { show: false } },
      data: [
        { value: onlineMeters.value, name: '在线', itemStyle: { color: '#52c41a' } },
        { value: offlineMeters.value, name: '离线', itemStyle: { color: '#ff4d4f' } },
      ],
    }],
  };
}

function buildAlarmTrendOptions(): any {
  const days: string[] = [];
  const alarmData: number[] = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    days.push(`${d.getMonth() + 1}/${d.getDate()}`);
    alarmData.push(Math.floor(Math.random() * 8));
  }

  return {
    title: { text: '近7日告警趋势', textStyle: { color: chartColors.value.text, fontSize: 14 }, left: 'center' },
    tooltip: themedTooltip({ axisPointer: { type: 'shadow' } }),
    grid: { top: 40, left: '3%', right: '4%', bottom: 10, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: days }),
    yAxis: themedAxis('y', { type: 'value', name: '告警数' }),
    series: [{
      type: 'bar', barWidth: '45%',
      data: alarmData.map((v) => ({
        value: v,
        itemStyle: { color: v >= 5 ? '#ff4d4f' : v >= 3 ? '#faad14' : '#1890ff' },
      })),
      label: { show: true, position: 'top', color: chartColors.value.textSecondary },
    }],
  };
}
</script>

<template>
  <div class="screen-page" :style="pageVars">
    <Spin :spinning="loading">
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">项目总数</span></template>
            <Statistic :value="projects.length" :value-style="{ color: THEME_COLORS.PROCESSING }" />
          </Card>
        </Col>
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">设备总数</span></template>
            <Statistic :value="totalMeters" :value-style="{ color: THEME_COLORS.PROCESSING }" />
          </Card>
        </Col>
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">在线设备</span></template>
            <Statistic :value="onlineMeters" :value-style="{ color: THEME_COLORS.SUCCESS }" />
          </Card>
        </Col>
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">离线设备</span></template>
            <Statistic :value="offlineMeters" :value-style="{ color: THEME_COLORS.ERROR }" />
          </Card>
        </Col>
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">活跃告警</span></template>
            <Statistic :value="alertCount" :value-style="{ color: THEME_COLORS.WARNING }" />
          </Card>
        </Col>
        <Col :span="4">
          <Card class="screen-card screen-card-sm" :bordered="false">
            <template #title><span class="screen-title">在线率</span></template>
            <Statistic
              :value="onlineRate"
              suffix="%"
              :value-style="{ color: onlineRate >= 95 ? THEME_COLORS.SUCCESS : THEME_COLORS.WARNING }"
            />
          </Card>
        </Col>
      </Row>

      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="16">
          <Card class="screen-card" :bordered="false">
            <template #title><span style="color: var(--text)">项目状态概览</span></template>
            <Table :columns="columns" :data-source="projects" row-key="id" :pagination="false" size="middle">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <Badge
                    :status="record.status === 'testing' ? 'processing' : record.status === 'completed' ? 'success' : 'default'"
                    :text="record.status === 'testing' ? '测试中' : record.status === 'completed' ? '已完成' : record.status"
                    style="color: var(--text-sec)"
                  />
                </template>
                <template v-if="column.key === 'online'">
                  <span class="screen-text">{{ record.online_count ?? '-' }} / {{ record.meter_count ?? '-' }}</span>
                </template>
                <template v-if="column.key === 'alert_count'">
                  <Tag v-if="record.alert_count > 0" color="red">{{ record.alert_count }}</Tag>
                  <span v-else :style="{ color: THEME_COLORS.SUCCESS }">0</span>
                </template>
                <template v-if="column.key === 'progress'">
                  <Progress
                    :percent="record.progress ?? 0"
                    :stroke-color="(record.progress ?? 0) === 100 ? '#52c41a' : '#1890ff'"
                    size="small"
                  />
                </template>
                <template v-if="column.key === 'action'">
                  <a class="screen-link" @click="goToProject(record.id)">详情大屏 →</a>
                </template>
              </template>
            </Table>
          </Card>
        </Col>

        <Col :span="8">
          <Card class="screen-card" :bordered="false" style="margin-bottom: 16px">
            <template #title><span style="color: var(--text)">设备在线率</span></template>
            <EchartsUI ref="onlineRateChartRef" height="200px" />
          </Card>
          <Card class="screen-card" :bordered="false" style="margin-bottom: 16px">
            <template #title><span style="color: var(--text)">堆栈监控</span></template>
            <EchartsUI ref="stackChartRef" height="220px" />
          </Card>
          <Card class="screen-card" :bordered="false" style="margin-bottom: 16px">
            <template #title><span style="color: var(--text)">告警趋势</span></template>
            <EchartsUI ref="alarmTrendChartRef" height="200px" />
          </Card>
        </Col>
      </Row>

      <Row :gutter="16">
        <Col :span="24">
          <Card class="screen-card" :bordered="false">
            <template #title><span style="color: var(--text)">事件统计</span></template>
            <Row :gutter="[16, 16]">
              <Col :span="6" v-for="e in eventStats" :key="e.type">
                <Card size="small" style="background: var(--bg)" :body-style="{ padding: '16px' }">
                  <template #title>
                    <span style="color: var(--text-muted); font-size: 12px">{{ e.type }}</span>
                  </template>
                  <Statistic :value="e.count" :value-style="{ color: e.color }" />
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </Spin>
  </div>
</template>

<style scoped>
.screen-page {
  background: var(--bg);
  min-height: 100vh;
  padding: 24px;
}

.screen-card {
  background: var(--bg-card) !important;
  border: none !important;
}

.screen-card :deep(.ant-card-head) {
  color: var(--text);
  border-bottom-color: var(--border);
}

.screen-card :deep(.ant-card-body) {
  padding: 16px;
}

.screen-card-sm :deep(.ant-card-body) {
  padding: 20px;
}

.screen-title {
  color: var(--text-sec);
}

.screen-text {
  color: var(--text-sec);
}

.screen-link {
  color: #40a9ff;
  cursor: pointer;
}

.screen-link:hover {
  color: #69b1ff;
}
</style>
