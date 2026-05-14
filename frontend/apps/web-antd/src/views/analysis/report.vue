<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref, watch } from 'vue';

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
import { useRouter } from 'vue-router';

import { getAnalysisReports, exportAnalysisReport } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';

const router = useRouter();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// Filters
const projectOptions = ref<{ label: string; value: number }[]>([]);
const dateRange = ref<[any, any] | null>(null);
const selectedProject = ref<number | undefined>(undefined);

// Chart refs
const qualityChartRef = ref<EchartsUIType>();
const { renderEcharts: renderQualityChart } = useEcharts(qualityChartRef);

const abnormalChartRef = ref<EchartsUIType>();
const { renderEcharts: renderAbnormalChart } = useEcharts(abnormalChartRef);

// Table columns
const columns = [
  { title: '报告编号', dataIndex: 'report_number', width: 160 },
  { title: '设备', dataIndex: 'meter_name', width: 130 },
  { title: '分析日期', dataIndex: 'analysis_date', width: 110 },
  { title: '电能增量', dataIndex: 'energy_increase', width: 100 },
  {
    title: '异常数',
    dataIndex: 'abnormal_count',
    width: 80,
    key: 'abnormal_count',
  },
  {
    title: '质量评分',
    dataIndex: 'quality_score',
    width: 100,
    key: 'quality_score',
  },
  { title: '操作', key: 'action', width: 160 },
];

// Summary stats
const summaryStats = computed(() => {
  const items = tableData.value;
  if (!items.length) return null;
  const avgScore =
    items.reduce((sum, i) => sum + (Number(i.quality_score) || 0), 0) /
    items.length;
  const totalAbnormal = items.reduce(
    (sum, i) => sum + (Number(i.abnormal_count) || 0),
    0,
  );
  const highQuality = items.filter(
    (i) => Number(i.quality_score) >= 90,
  ).length;
  return { avgScore: avgScore.toFixed(1), totalAbnormal, highQuality };
});

async function fetchProjects() {
  try {
    const res = await getProjectList();
    const items = res.items || res || [];
    projectOptions.value = items.map((p: any) => ({
      label: p.name,
      value: p.id,
    }));
  } catch {
    // Ignore
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const res = await getAnalysisReports({
      project_id: selectedProject.value,
      page: currentPage.value,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    renderCharts();
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  const items = tableData.value;
  if (!items.length) return;

  // Quality score trend bar chart
  const dates = items.map((i: any) => i.analysis_date || '-');
  const scores = items.map((i: any) => Number(i.quality_score) || 0);
  const scoreColors = scores.map((s: number) =>
    s >= 90 ? '#52c41a' : s >= 70 ? '#faad14' : '#ff4d4f',
  );

  renderQualityChart({
    title: {
      text: '质量评分趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = params[0];
        return `${p.axisValue}<br/>质量评分: <b>${p.value}</b>`;
      },
    },
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '评分',
      min: 0,
      max: 100,
    },
    series: [
      {
        type: 'bar',
        data: scores.map((val: number, idx: number) => ({
          value: val,
          itemStyle: { color: scoreColors[idx] },
        })),
        barWidth: '40%',
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
        },
      },
    ],
  });

  // Abnormal count trend bar chart
  const abnormalCounts = items.map((i: any) => Number(i.abnormal_count) || 0);

  renderAbnormalChart({
    title: {
      text: '异常数量趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: '异常数',
      min: 0,
    },
    series: [
      {
        type: 'bar',
        data: abnormalCounts,
        barWidth: '40%',
        itemStyle: {
          color: (params: any) =>
            params.value > 3 ? '#ff4d4f' : params.value > 0 ? '#faad14' : '#52c41a',
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
        },
      },
    ],
  });
}

function handleViewDetail(record: any) {
  router.push({
    path: '/analysis/daily',
    query: {
      meter_id: record.meter_id || record.id,
      date: record.analysis_date,
    },
  });
}

async function handleExportPDF(record: any) {
  try {
    const blob = await exportAnalysisReport(record.id);
    const url = window.URL.createObjectURL(blob as any);
    const a = document.createElement('a');
    a.href = url;
    a.download = `分析报告_${record.report_number || record.id}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败');
  }
}

function handlePageChange(page: number, size: number) {
  currentPage.value = page;
  pageSize.value = size;
  fetchData();
}

onMounted(() => {
  fetchProjects();
  fetchData();
});

watch(selectedProject, () => {
  currentPage.value = 1;
  fetchData();
});
</script>

<template>
  <Page auto-content-height>
    <!-- Summary stats -->
    <Row v-if="summaryStats" :gutter="16" style="margin-bottom: 16px">
      <Col :span="8">
        <Card>
          <Statistic
            title="平均质量评分"
            :value="summaryStats.avgScore"
            suffix="/ 100"
          />
        </Card>
      </Col>
      <Col :span="8">
        <Card>
          <Statistic
            title="异常总数"
            :value="summaryStats.totalAbnormal"
            :value-style="{
              color: summaryStats.totalAbnormal > 0 ? '#fa8c16' : undefined,
            }"
          />
        </Card>
      </Col>
      <Col :span="8">
        <Card>
          <Statistic
            title="高质量报告数 (>= 90分)"
            :value="summaryStats.highQuality"
            :suffix="`/ ${tableData.length}`"
          />
        </Card>
      </Col>
    </Row>

    <!-- Filter bar -->
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item label="项目">
          <Select
            v-model:value="selectedProject"
            placeholder="全部项目"
            :options="projectOptions"
            allow-clear
            style="width: 200px"
            show-search
            :filter-option="
              (input: string, option: any) =>
                option.label?.toLowerCase().includes(input.toLowerCase())
            "
          />
        </Form.Item>
        <Form.Item label="日期范围">
          <DatePicker
            :value="dateRange?.[0]"
            placeholder="开始日期"
            style="width: 140px"
            @change="
              (val: any) => {
                if (!dateRange) dateRange = [null, null];
                dateRange[0] = val;
              }
            "
          />
          <span style="margin: 0 8px; color: #999">-</span>
          <DatePicker
            :value="dateRange?.[1]"
            placeholder="结束日期"
            style="width: 140px"
            @change="
              (val: any) => {
                if (!dateRange) dateRange = [null, null];
                dateRange[1] = val;
              }
            "
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" @click="fetchData" :loading="loading">
            查询
          </Button>
        </Form.Item>
        <Form.Item>
          <Button @click="fetchData">刷新</Button>
        </Form.Item>
      </Form>
    </Card>

    <!-- Charts row -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="12">
        <Card :bordered="false" title="质量评分趋势">
          <EchartsUI ref="qualityChartRef" height="280px" />
        </Card>
      </Col>
      <Col :span="12">
        <Card :bordered="false" title="异常数量趋势">
          <EchartsUI ref="abnormalChartRef" height="280px" />
        </Card>
      </Col>
    </Row>

    <!-- Report table -->
    <Card :bordered="false" title="分析报告列表">
      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        row-key="id"
        :pagination="{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t: number) => `共 ${t} 条`,
          onChange: handlePageChange,
        }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'quality_score'">
            <Tag
              :color="
                Number(record.quality_score) >= 90
                  ? 'green'
                  : Number(record.quality_score) >= 70
                    ? 'orange'
                    : 'red'
              "
            >
              {{ record.quality_score }}
            </Tag>
          </template>
          <template v-if="column.key === 'abnormal_count'">
            <Tag :color="Number(record.abnormal_count) > 0 ? 'red' : 'green'">
              {{ record.abnormal_count || 0 }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button
                type="link"
                size="small"
                @click="handleViewDetail(record)"
              >
                查看详情
              </Button>
              <Button
                type="link"
                size="small"
                @click="handleExportPDF(record)"
              >
                导出PDF
              </Button>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
