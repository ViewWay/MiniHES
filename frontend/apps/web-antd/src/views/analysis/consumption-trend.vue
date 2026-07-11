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
  Row,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getConsumptionTrend } from '#/api/modules/analysis';
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
const { renderEcharts: renderLineChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '表名', dataIndex: 'meter_name', width: 140 },
  { title: '总用电量', dataIndex: 'total_consumption', width: 120 },
  { title: '日均用电', dataIndex: 'avg_daily', width: 120 },
  { title: '采集天数', dataIndex: 'days_collected', width: 100 },
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
    const res = await getConsumptionTrend(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderLine();
  } finally {
    loading.value = false;
  }
}

function renderLine() {
  const data = chartsData.value.daily_trend || { labels: [], series: {} };
  renderLineChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: { top: 30, left: '3%', right: '4%', bottom: 20, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: data.labels }),
    yAxis: themedAxis('y', { type: 'value', name: '用电量' }),
    series: [
      {
        name: '用电量',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        data: data.series.consumption || [],
        itemStyle: { color: '#1890ff' },
      },
    ],
  });
}

watchThemeAndRerender(renderLine);

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
          <Statistic title="总用电量" :value="summary.total_consumption" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="日均用电" :value="summary.avg_daily" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="峰值日" :value="summary.peak_day" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="用电量趋势" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="320px" />
    </Card>

    <Card :bordered="false" title="按表计汇总">
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
        row-key="meter_id"
        size="middle"
        @change="handleTableChange"
      />
    </Card>
  </Page>
</template>
