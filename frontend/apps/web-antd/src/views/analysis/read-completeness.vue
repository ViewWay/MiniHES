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
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getReadCompleteness } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, watchThemeAndRerender } = useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const selectedProject = ref<number | undefined>(undefined);
const projectOptions = ref<{ label: string; value: number }[]>([]);
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderBarChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '表名', dataIndex: 'meter_name', width: 140 },
  { title: '总点位', dataIndex: 'total_points', width: 100 },
  { title: '成功点位', dataIndex: 'success_points', width: 100 },
  { title: '失败点位', dataIndex: 'failed_points', width: 100 },
  { title: '完整率', key: 'completeness', width: 160, dataIndex: 'completeness' },
];

async function fetchProjects() {
  try {
    const res = await getProjectList();
    projectOptions.value = (res.items || res || []).map((item: any) => ({
      label: item.name,
      value: item.id,
    }));
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
    };
    if (dateRange.value?.length === 2) {
      params.date_from = dateRange.value[0]?.format?.('YYYY-MM-DD');
      params.date_to = dateRange.value[1]?.format?.('YYYY-MM-DD');
    }
    if (selectedProject.value !== undefined) {
      params.project_id = selectedProject.value;
    }
    const res = await getReadCompleteness(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderBar();
  } catch {
    message.error('抄表完整率数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderBar() {
  const data = chartsData.value.distribution || { labels: [], series: {} };
  renderBarChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: { top: 30, left: '3%', right: '4%', bottom: 20, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: data.labels }),
    yAxis: themedAxis('y', { type: 'value', name: '设备数' }),
    series: [
      {
        type: 'bar',
        data: data.series.count || [],
        itemStyle: { color: '#52c41a' },
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
  selectedProject.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function completenessColor(val: number) {
  if (val >= 98) return '#52c41a';
  if (val >= 90) return '#faad14';
  return '#ff4d4f';
}

onMounted(() => {
  fetchProjects();
  fetchData();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item label="日期范围">
          <RangePicker v-model:value="dateRange" style="width: 260px" />
        </Form.Item>
        <Form.Item label="项目">
          <Select
            v-model:value="selectedProject"
            allow-clear
            placeholder="全部项目"
            style="width: 160px"
            :options="projectOptions"
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
          <Statistic title="系统完整率" :value="summary.completeness" suffix="%" :value-style="{ color: '#52c41a' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="总点位" :value="summary.total_points" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="成功点位" :value="summary.success_points" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="失败点位" :value="summary.failed_points" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="低于SLA" :value="summary.below_sla" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="完整率分布" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="抄表完整率明细">
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
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'completeness'">
            <Progress
              :percent="record.completeness"
              :stroke-color="completenessColor(record.completeness)"
              size="small"
            />
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
