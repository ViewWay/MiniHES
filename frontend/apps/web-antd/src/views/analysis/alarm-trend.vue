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

import { getAlarmTrend } from '#/api/modules/analysis';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderStackedChart } = useEcharts(chartRef);

const columns = [
  { title: '告警类型', dataIndex: 'alarm_type', width: 120 },
  { title: '严重度', key: 'severity', width: 100, dataIndex: 'severity' },
  { title: '告警信息', dataIndex: 'alarm_message', ellipsis: true },
  { title: '表计ID', dataIndex: 'meter_id', width: 90 },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
  { title: '已处理', key: 'is_handled', width: 80 },
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
    const res = await getAlarmTrend(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderChart();
  } catch {
    message.error('告警趋势数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderChart() {
  const data = chartsData.value.weekly_trend || { labels: [], series: {} };
  renderStackedChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ data: ['严重', '警告', '信息'] }),
    grid: { top: 40, left: '3%', right: '4%', bottom: 30, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: data.labels }),
    yAxis: themedAxis('y', { type: 'value', name: '告警数' }),
    series: [
      { name: '严重', type: 'bar', stack: 'total', data: data.series.critical || [], itemStyle: { color: '#ff4d4f' } },
      { name: '警告', type: 'bar', stack: 'total', data: data.series.warning || [], itemStyle: { color: '#faad14' } },
      { name: '信息', type: 'bar', stack: 'total', data: data.series.info || [], itemStyle: { color: '#1890ff' } },
    ],
  });
}

watchThemeAndRerender(renderChart);

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

function severityColor(sev: string) {
  if (sev === 'critical') return 'red';
  if (sev === 'warning') return 'orange';
  return 'blue';
}

function severityLabel(sev: string) {
  if (sev === 'critical') return '严重';
  if (sev === 'warning') return '警告';
  return '信息';
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
      <Col :span="12">
        <Card>
          <Statistic title="总告警数（统计区间）" :value="summary.total_alarms" />
        </Card>
      </Col>
      <Col :span="12">
        <Card>
          <Statistic title="周均告警" :value="summary.weekly_avg" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="周告警趋势（按严重度堆叠）" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="320px" />
    </Card>

    <Card :bordered="false" title="告警明细">
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
          <template v-if="column.key === 'severity'">
            <Tag :color="severityColor(record.severity)">
              {{ severityLabel(record.severity) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'is_handled'">
            <Tag :color="record.is_handled ? 'green' : 'red'">
              {{ record.is_handled ? '已处理' : '未处理' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
