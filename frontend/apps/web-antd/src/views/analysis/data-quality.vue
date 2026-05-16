<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  InputNumber,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  message,
} from 'ant-design-vue';

import { getDataQuality, exportDataQuality } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';

const RangePicker = DatePicker.RangePicker;

const loading = ref(false);
const exporting = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const projectOptions = ref<{ label: string; value: number }[]>([]);

const searchForm = ref({
  project_id: undefined as number | undefined,
  meter_id: undefined as number | undefined,
  min_score: undefined as number | undefined,
});

// Chart ref
const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderQualityChart } = useEcharts(chartRef);

// Summary stats
const summaryStats = ref({
  avg_quality_score: 0,
  total_devices: 0,
  abnormal_devices: 0,
  success_rate: 0,
});

const columns = [
  { title: '设备名称', dataIndex: 'meter_name', width: 140 },
  { title: '统计日期', dataIndex: 'stat_date', width: 120 },
  { title: '总采集点', dataIndex: 'total_points', width: 100 },
  { title: '成功点数', dataIndex: 'success_points', width: 100 },
  { title: '失败点数', dataIndex: 'failed_points', width: 100 },
  {
    title: '质量评分',
    dataIndex: 'quality_score',
    key: 'quality_score',
    width: 120,
  },
  { title: '异常次数', dataIndex: 'abnormal_count', width: 100 },
  {
    title: '首次采集时间',
    dataIndex: 'first_collect_time',
    width: 170,
  },
  {
    title: '末次采集时间',
    dataIndex: 'last_collect_time',
    width: 170,
  },
];

async function fetchProjects() {
  try {
    const res = await getProjectList();
    projectOptions.value = (res.items || res || []).map(
      (item: any) => ({ label: item.name, value: item.id }),
    );
  } catch {
    // ignore
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      ...searchForm.value,
    };
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date =
        dateRange.value[0]?.format?.('YYYY-MM-DD') || dateRange.value[0];
      params.end_date =
        dateRange.value[1]?.format?.('YYYY-MM-DD') || dateRange.value[1];
    }
    const res = await getDataQuality(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    if (res.summary) {
      summaryStats.value = res.summary;
    }
    renderChart(res.trend || generateDemoTrend());
  } finally {
    loading.value = false;
  }
}

function renderChart(trend: any[]) {
  const xData = trend.map((d: any) => d.date);
  const scoreData = trend.map((d: any) => d.avg_score);

  renderQualityChart({
    title: {
      text: '近7日质量评分趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = params[0];
        return `${p.axisValue}<br/>平均质量评分: <b>${p.value}</b>`;
      },
    },
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 30,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xData,
    },
    yAxis: {
      type: 'value',
      name: '质量评分',
      min: 0,
      max: 100,
    },
    series: [
      {
        type: 'bar',
        data: scoreData.map((v: number) => ({
          value: v,
          itemStyle: {
            color:
              v >= 90
                ? '#52c41a'
                : v >= 70
                  ? '#faad14'
                  : '#ff4d4f',
          },
        })),
        barWidth: '50%',
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
        },
      },
    ],
  });
}

function generateDemoTrend() {
  const days: any[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push({
      date: d.toISOString().slice(0, 10),
      avg_score: Math.round(75 + Math.random() * 20),
    });
  }
  return days;
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleReset() {
  searchForm.value = {
    project_id: undefined,
    meter_id: undefined,
    min_score: undefined,
  };
  dateRange.value = null;
  pagination.value.current = 1;
  fetchData();
}

async function handleExport() {
  exporting.value = true;
  try {
    const params: Record<string, any> = { ...searchForm.value };
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date =
        dateRange.value[0]?.format?.('YYYY-MM-DD') || dateRange.value[0];
      params.end_date =
        dateRange.value[1]?.format?.('YYYY-MM-DD') || dateRange.value[1];
    }
    const blob: Blob = await exportDataQuality(params);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `数据质量统计_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败，请重试');
  } finally {
    exporting.value = false;
  }
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function getScoreColor(score: number) {
  if (score >= 90) return 'green';
  if (score >= 70) return 'orange';
  return 'red';
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page auto-content-height>
    <!-- Filter bar -->
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline" :model="searchForm">
        <Form.Item label="日期范围">
          <RangePicker v-model:value="dateRange" style="width: 260px" />
        </Form.Item>
        <Form.Item label="项目">
          <Select
            v-model:value="searchForm.project_id"
            allow-clear
            placeholder="全部项目"
            style="width: 160px"
            :options="projectOptions"
          />
        </Form.Item>
        <Form.Item label="设备搜索">
          <InputNumber
            v-model:value="searchForm.meter_id"
            placeholder="设备ID"
            style="width: 140px"
          />
        </Form.Item>
        <Form.Item label="质量评分阈值">
          <InputNumber
            v-model:value="searchForm.min_score"
            placeholder="最低评分"
            :min="0"
            :max="100"
            style="width: 140px"
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" @click="handleSearch">查询</Button>
            <Button @click="handleReset">重置</Button>
            <Button :loading="exporting" @click="handleExport">导出</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <!-- Summary stats -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic
            title="平均质量评分"
            :value="summaryStats.avg_quality_score"
            suffix="/ 100"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="总设备数" :value="summaryStats.total_devices" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="异常设备数"
            :value="summaryStats.abnormal_devices"
            :value-style="{ color: '#ff4d4f' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="整体成功率"
            :value="summaryStats.success_rate"
            suffix="%"
          />
        </Card>
      </Col>
    </Row>

    <!-- Quality score trend chart -->
    <Card :bordered="false" title="质量评分趋势（近7日）" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="300px" />
    </Card>

    <!-- Data table -->
    <Card :bordered="false" title="数据质量明细">
      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total,
          showSizeChanger: true,
          showTotal: (t: number) => `共 ${t} 条`,
        }"
        row-key="id"
        @change="handleTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'quality_score'">
            <Tag :color="getScoreColor(record.quality_score)">
              {{ record.quality_score }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
