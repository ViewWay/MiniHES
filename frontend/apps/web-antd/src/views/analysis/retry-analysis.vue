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
  message,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getRetryAnalysis } from '#/api/modules/analysis';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, watchThemeAndRerender } = useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderBarChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '重试次数', dataIndex: 'retry_count', width: 100 },
  { title: '错误码', dataIndex: 'error_code', width: 120 },
  { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
  { title: '状态', key: 'status', width: 100, dataIndex: 'status' },
  { title: '耗时(ms)', dataIndex: 'duration_ms', width: 110 },
  { title: '开始时间', dataIndex: 'start_time', width: 170 },
];

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]?.format?.('YYYY-MM-DD');
      params.date_to = dateRange.value[1]?.format?.('YYYY-MM-DD');
    }
    const res = await getRetryAnalysis(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderBar();
  } catch {
    message.error('重试分析数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderBar() {
  const data = chartsData.value.retry_distribution || { labels: [], series: {} };
  renderBarChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: { top: 30, left: '3%', right: '4%', bottom: 20, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: data.labels }),
    yAxis: themedAxis('y', { type: 'value', name: '设备数' }),
    series: [
      {
        type: 'bar',
        data: data.series.count || [],
        itemStyle: { color: '#faad14' },
        barWidth: '50%',
      },
    ],
  });
}

watchThemeAndRerender(renderBar);

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleReset() {
  dateRange.value = null;
  pagination.value.current = 1;
  fetchData();
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

onMounted(fetchData);
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item label="日期范围">
          <RangePicker v-model:value="dateRange" style="width: 260px" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" @click="handleSearch">查询</Button>
            <Button @click="handleReset">重置</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="总重试次数" :value="summary.total_retries" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="平均重试" :value="summary.avg_retries" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="高重试设备(≥3次)" :value="summary.high_retry_count" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="涉及设备" :value="summary.total_devices" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="重试次数分布" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="重试明细">
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
        size="middle"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="record.status === 'success' ? 'green' : 'red'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
