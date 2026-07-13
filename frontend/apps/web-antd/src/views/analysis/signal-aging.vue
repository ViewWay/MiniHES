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
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getSignalAging } from '#/api/modules/analysis';
import { useChartTheme } from '#/composables/useChartTheme';

const { themedTooltip, themedLegend, watchThemeAndRerender } = useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderPieChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '表名', dataIndex: 'meter_name', width: 140 },
  { title: '信号强度', key: 'signal', width: 160, dataIndex: 'signal_strength' },
  { title: '健康度', key: 'health', width: 100 },
  { title: '最后通信', dataIndex: 'last_comm_time', width: 170 },
  { title: '在线', key: 'online_status', width: 80 },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getSignalAging({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderPie();
  } finally {
    loading.value = false;
  }
}

function renderPie() {
  const data = chartsData.value.health_distribution || { labels: [], series: {} };
  renderPieChart({
    tooltip: themedTooltip({ trigger: 'item' }),
    legend: themedLegend({ bottom: 0 }),
    color: ['#52c41a', '#faad14', '#ff4d4f'],
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

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function healthColor(health: string) {
  if (health === 'good') return 'green';
  if (health === 'warning') return 'orange';
  return 'red';
}

function healthLabel(health: string) {
  if (health === 'good') return '良好';
  if (health === 'warning') return '警告';
  return '严重';
}

function signalColor(val: number) {
  if (val >= 60) return '#52c41a';
  if (val >= 30) return '#faad14';
  return '#ff4d4f';
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
          <Statistic title="总设备" :value="summary.total_devices" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="良好 (>60)" :value="summary.good" :value-style="{ color: '#52c41a' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="警告 (30-60)" :value="summary.warning" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="严重 (<30)" :value="summary.critical" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="信号健康分布" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="信号老化明细">
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
          <template v-if="column.key === 'signal'">
            <Progress
              :percent="record.signal_strength || 0"
              :stroke-color="signalColor(record.signal_strength || 0)"
              size="small"
            />
          </template>
          <template v-else-if="column.key === 'health'">
            <Tag :color="healthColor(record.health)">
              {{ healthLabel(record.health) }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'online_status'">
            <Tag :color="record.online_status ? 'green' : 'red'">
              {{ record.online_status ? '在线' : '离线' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
