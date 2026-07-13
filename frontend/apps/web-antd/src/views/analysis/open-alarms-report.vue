<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  Form,
  message,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getOpenAlarmsReport } from '#/api/modules/analysis';
import { useChartTheme } from '#/composables/useChartTheme';

const { themedTooltip, themedLegend, watchThemeAndRerender } = useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const summary = ref<any>({});
const chartsData = ref<any>({});
const filterSeverity = ref<string | undefined>(undefined);

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderPieChart } = useEcharts(chartRef);

const columns = [
  { title: '告警类型', dataIndex: 'alarm_type', width: 120 },
  { title: '严重度', key: 'severity', width: 100, dataIndex: 'severity' },
  { title: '告警信息', dataIndex: 'alarm_message', ellipsis: true },
  { title: '告警值', dataIndex: 'alarm_value', width: 100 },
  { title: '阈值', dataIndex: 'threshold_value', width: 100 },
  { title: '表计ID', dataIndex: 'meter_id', width: 90 },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
  { title: '持续(小时)', dataIndex: 'age_hours', width: 110 },
];

const severityOptions = [
  { label: '全部', value: undefined },
  { label: '严重', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '信息', value: 'info' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getOpenAlarmsReport({
      severity: filterSeverity.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderPie();
  } catch {
    message.error('未确认告报表数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderPie() {
  const data = chartsData.value.by_severity || { labels: [], series: {} };
  renderPieChart({
    tooltip: themedTooltip({ trigger: 'item' }),
    legend: themedLegend({ bottom: 0 }),
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.labels.map((label: string, i: number) => ({
          name: label,
          value: (data.series.count || [])[i] || 0,
        })),
      },
    ],
  });
}

watchThemeAndRerender(renderPie);

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleReset() {
  filterSeverity.value = undefined;
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
        <Form.Item label="严重度">
          <Select
            v-model:value="filterSeverity"
            style="width: 140px"
            :options="severityOptions"
          />
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
          <Statistic title="未确认总数" :value="summary.total_open" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="严重" :value="summary.critical" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="警告" :value="summary.major" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="平均持续(小时)" :value="summary.avg_age_hours" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="严重度分布" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="未确认告警列表">
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
        </template>
      </Table>
    </Card>
  </Page>
</template>
