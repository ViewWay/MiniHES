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
  Row,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getDeviceHealth } from '#/api/modules/analysis';
import { useChartTheme } from '#/composables/useChartTheme';

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderBarChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '表名', dataIndex: 'meter_name', width: 140 },
  { title: '型号', dataIndex: 'model', width: 120 },
  { title: '固件', dataIndex: 'firmware_version', width: 120 },
  { title: '在线', key: 'online_status', width: 80 },
  { title: '信号', dataIndex: 'signal_strength', width: 80 },
  { title: '健康度', key: 'health', width: 100, dataIndex: 'health' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getDeviceHealth({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderChart();
  } finally {
    loading.value = false;
  }
}

function renderChart() {
  const data = chartsData.value.by_model || { labels: [], series: {} };
  renderBarChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ data: ['总数', '健康', '告警'] }),
    grid: { top: 40, left: '3%', right: '4%', bottom: 30, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: data.labels }),
    yAxis: themedAxis('y', { type: 'value', name: '设备数' }),
    series: [
      { name: '总数', type: 'bar', data: data.series.total || [] },
      { name: '健康', type: 'bar', data: data.series.healthy || [], itemStyle: { color: '#52c41a' } },
      { name: '告警', type: 'bar', data: data.series.alert || [], itemStyle: { color: '#ff4d4f' } },
    ],
  });
}

watchThemeAndRerender(renderChart);

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function healthColor(health: string) {
  if (health === 'healthy') return 'green';
  if (health === 'watch') return 'orange';
  return 'red';
}

function healthLabel(health: string) {
  if (health === 'healthy') return '健康';
  if (health === 'watch') return '关注';
  return '告警';
}

onMounted(fetchData);
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item>
          <Space>
            <Button type="primary" @click="fetchData">刷新</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="总设备" :value="summary.total_meters" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="健康分" :value="summary.health_score" suffix="/100" :value-style="{ color: '#52c41a' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="健康" :value="summary.healthy" :value-style="{ color: '#52c41a' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="关注" :value="summary.watch" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="告警" :value="summary.alert" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="按型号分组健康度" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="设备健康明细">
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
          <template v-if="column.key === 'online_status'">
            <Tag :color="record.online_status ? 'green' : 'red'">
              {{ record.online_status ? '在线' : '离线' }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'health'">
            <Tag :color="healthColor(record.health)">
              {{ healthLabel(record.health) }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
