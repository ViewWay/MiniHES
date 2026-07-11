<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  message,
} from 'ant-design-vue';
import dayjs from 'dayjs';

import { getCompareAnalysis } from '#/api/modules/analysis';
import { getMeterList } from '#/api/modules/meter';
import { useChartTheme } from '#/composables/useChartTheme';

const { RangePicker } = DatePicker;

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const compareResult = ref<any>(null);
const meterOptions = ref<{ label: string; value: number }[]>([]);
const metersLoading = ref(false);

const searchForm = ref({
  meter_ids: [] as number[],
  dateRange: undefined as [any, any] | undefined,
});

// Chart refs
const comparisonChartRef = ref<EchartsUIType>();
const { renderEcharts: renderComparisonChart } = useEcharts(comparisonChartRef);

const deviationChartRef = ref<EchartsUIType>();
const { renderEcharts: renderDeviationChart } = useEcharts(deviationChartRef);

// Fetch meter list for multi-select
async function fetchMeters() {
  metersLoading.value = true;
  try {
    const res = await getMeterList({ page: 1, page_size: 200 });
    const items = res.items || res || [];
    meterOptions.value = items.map((m: any) => ({
      label: `${m.meter_name || m.serial_number} (ID: ${m.id})`,
      value: m.id,
    }));
  } catch {
    // Fallback: allow manual input
  } finally {
    metersLoading.value = false;
  }
}

onMounted(() => {
  fetchMeters();
});

const hasResult = computed(() => !!compareResult.value);

// Comparison metrics columns
const metricsColumns = [
  { title: '设备', dataIndex: 'meter_name', width: 150 },
  { title: '总电能 (kWh)', dataIndex: 'total_energy', width: 120 },
  { title: '日均值 (kWh)', dataIndex: 'daily_avg', width: 120 },
  { title: '最大需量 (kW)', dataIndex: 'max_demand', width: 130 },
  { title: '偏差率 (%)', dataIndex: 'deviation_rate', width: 110 },
  {
    title: '数据完整率',
    dataIndex: 'completeness',
    key: 'completeness',
    width: 120,
  },
  {
    title: '异常标记',
    dataIndex: 'anomaly_flags',
    key: 'anomaly_flags',
  },
];

async function handleCompare() {
  if (searchForm.value.meter_ids.length < 2) {
    message.warning('请选择至少2个设备进行对比');
    return;
  }
  if (!searchForm.value.dateRange) {
    message.warning('请选择日期范围');
    return;
  }

  loading.value = true;
  try {
    const [startDate, endDate] = searchForm.value.dateRange!;
    compareResult.value = await getCompareAnalysis({
      meter_ids: searchForm.value.meter_ids,
      start_date: startDate?.format('YYYY-MM-DD') || '',
      end_date: endDate?.format('YYYY-MM-DD') || '',
    });
    renderCharts();
  } catch {
    message.error('对比分析请求失败');
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  const data = compareResult.value;
  if (!data) return;

  // Render energy comparison line chart
  const seriesData = data.series || [];
  const xData =
    data.x_axis ||
    Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

  renderComparisonChart({
    tooltip: themedTooltip({
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    }),
    legend: themedLegend({
      data: seriesData.map((s: any) => s.name),
      bottom: 0,
    }),
    grid: {
      top: 30,
      left: '3%',
      right: '4%',
      bottom: 60,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      boundaryGap: false,
      data: xData,
    }),
    yAxis: themedAxis('y', {
      type: 'value',
      name: '电能 (kWh)',
      axisLabel: { formatter: '{value}' },
    }),
    series: seriesData.map((s: any) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data,
      emphasis: { focus: 'series' },
    })),
  });

  // Render deviation bar chart
  const metricsData = data.metrics || [];

  renderDeviationChart({
    tooltip: themedTooltip({
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    }),
    legend: themedLegend({
      bottom: 0,
      data: ['偏差率', '完整率'],
    }),
    grid: {
      top: 30,
      left: '3%',
      right: '4%',
      bottom: 40,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      data: metricsData.map((m: any) => m.meter_name),
    }),
    yAxis: themedAxis('y', { type: 'value', name: '%' }),
    series: [
      {
        name: '偏差率',
        type: 'bar',
        data: metricsData.map((m: any) => m.deviation_rate ?? 0),
      },
      {
        name: '完整率',
        type: 'bar',
        data: metricsData.map((m: any) => m.completeness ?? 100),
      },
    ],
  });
}

watchThemeAndRerender(renderCharts);

const tableData = computed(() => {
  if (!compareResult.value) return [];
  return compareResult.value.metrics || [];
});

const summaryStats = computed(() => {
  if (!compareResult.value) return null;
  const d = compareResult.value;
  return {
    todayTotal: d.summary?.today_total ?? '-',
    yesterdayTotal: d.summary?.yesterday_total ?? '-',
    deviationRate: d.summary?.deviation_rate ?? '-',
    anomalyCount: d.summary?.anomaly_count ?? 0,
  };
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="对比分析" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item label="选择设备">
          <Select
            v-model:value="searchForm.meter_ids"
            mode="multiple"
            placeholder="请选择设备"
            :options="meterOptions"
            :loading="metersLoading"
            style="min-width: 350px"
            :max-tag-count="3"
            allow-clear
            show-search
            :filter-option="
              (input: string, option: any) =>
                option.label?.toLowerCase().includes(input.toLowerCase())
            "
          />
        </Form.Item>
        <Form.Item label="日期范围">
          <RangePicker
            v-model:value="searchForm.dateRange"
            style="width: 280px"
            :presets="[
              {
                label: '最近7天',
                value: [dayjs().subtract(7, 'day'), dayjs()],
              },
              {
                label: '最近30天',
                value: [dayjs().subtract(30, 'day'), dayjs()],
              },
              {
                label: '本月',
                value: [dayjs().startOf('month'), dayjs()],
              },
            ]"
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" @click="handleCompare" :loading="loading">
              查询
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <template v-if="hasResult">
      <!-- Summary statistics -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Card>
            <Statistic
              title="今日总电能 (kWh)"
              :value="summaryStats?.todayTotal"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="昨日总电能 (kWh)"
              :value="summaryStats?.yesterdayTotal"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="日间偏差率 (%)"
              :value="summaryStats?.deviationRate"
              :value-style="{
                color:
                  Number(summaryStats?.deviationRate) > 5 ? '#ff4d4f' : undefined,
              }"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="异常事件数"
              :value="summaryStats?.anomalyCount"
              :value-style="{
                color: Number(summaryStats?.anomalyCount) > 0 ? '#fa8c16' : undefined,
              }"
            />
          </Card>
        </Col>
      </Row>

      <!-- Energy comparison line chart -->
      <Card :bordered="false" title="电能数据对比曲线" style="margin-bottom: 16px">
        <EchartsUI ref="comparisonChartRef" height="300px" />
      </Card>

      <!-- Deviation bar chart -->
      <Card
        :bordered="false"
        title="数据偏差率对比"
        style="margin-bottom: 16px"
      >
        <EchartsUI ref="deviationChartRef" height="300px" />
      </Card>

      <!-- Comparison metrics table -->
      <Card :bordered="false" title="对比指标明细">
        <Table
          :columns="metricsColumns"
          :data-source="tableData"
          row-key="meter_name"
          :pagination="false"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'completeness'">
              <span>{{ record.completeness ?? '-' }}%</span>
            </template>
            <template v-if="column.key === 'anomaly_flags'">
              <Space>
                <Tag
                  v-if="record.anomaly_flags && record.anomaly_flags !== '无'"
                  color="orange"
                >
                  {{ record.anomaly_flags }}
                </Tag>
                <Tag v-else color="green">正常</Tag>
              </Space>
            </template>
          </template>
        </Table>
      </Card>
    </template>

    <!-- Empty state -->
    <Card
      v-if="!hasResult && !loading"
      :bordered="false"
      style="margin-top: 16px"
    >
      <div style="color: #999; text-align: center; padding: 60px 0">
        <p style="font-size: 16px; margin-bottom: 8px">选择设备并指定日期范围开始对比分析</p>
        <p style="font-size: 12px; color: #bbb">PRD 3.3.1 — 今日 vs 昨日对比，检测数据突变</p>
      </div>
    </Card>
  </Page>
</template>
