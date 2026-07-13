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
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import { getCommSuccessRate } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const selectedProject = ref<number | undefined>(undefined);
const projectOptions = ref<{ label: string; value: number }[]>([]);
const summary = ref<any>({});

const trendChartRef = ref<EchartsUIType>();
const { renderEcharts: renderTrendChart } = useEcharts(trendChartRef);

const reasonChartRef = ref<EchartsUIType>();
const { renderEcharts: renderReasonChart } = useEcharts(reasonChartRef);

const columns = [
  { title: '日期', dataIndex: 'date', width: 170 },
  { title: '总尝试', dataIndex: 'total_attempts', width: 100 },
  { title: '成功', dataIndex: 'success', width: 100 },
  { title: '失败', dataIndex: 'failed', width: 100 },
  { title: '成功率', key: 'success_rate', width: 110, dataIndex: 'success_rate' },
  { title: '耗时(ms)', dataIndex: 'duration_ms', width: 110 },
  { title: '状态', key: 'status', width: 100, dataIndex: 'status' },
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
    const res = await getCommSuccessRate(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    renderCharts(res.charts || {});
  } catch {
    message.error('通信成功率数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderCharts(charts: any) {
  const trend = charts.daily_trend || { labels: [], series: {} };
  renderTrendChart({
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ data: ['尝试次数', '成功率'] }),
    grid: { top: 40, left: '3%', right: '4%', bottom: 40, containLabel: true },
    xAxis: themedAxis('x', { type: 'category', data: trend.labels }),
    yAxis: [
      themedAxis('y', { type: 'value', name: '尝试次数' }),
      themedAxis('y', {
        type: 'value',
        name: '成功率%',
        min: 0,
        max: 100,
        position: 'right',
      }),
    ],
    series: [
      { name: '尝试次数', type: 'bar', data: trend.series.attempts || [] },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: trend.series.success_rate || [],
      },
    ],
  });

  const reasons = charts.failure_reasons || { labels: [], series: {} };
  renderReasonChart({
    tooltip: themedTooltip({ trigger: 'item' }),
    legend: themedLegend({ bottom: 0 }),
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: reasons.labels.map((label: string, i: number) => ({
          name: label,
          value: (reasons.series.count || [])[i] || 0,
        })),
      },
    ],
  });
}

watchThemeAndRerender(() => renderCharts({}));

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
          <Statistic title="总尝试次数" :value="summary.total_attempts" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="成功率"
            :value="summary.success_rate"
            suffix="%"
            :value-style="{ color: '#52c41a' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="失败率"
            :value="summary.failure_rate"
            suffix="%"
            :value-style="{ color: '#ff4d4f' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="失败总数"
            :value="summary.total_failed"
            :value-style="{ color: '#faad14' }"
          />
        </Card>
      </Col>
    </Row>

    <Card
      v-if="summary.demo"
      :bordered="false"
      style="margin-bottom: 16px"
      :body-style="{ padding: '8px 16px' }"
    >
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">
        当前查询范围内无采集数据
      </span>
    </Card>

    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="14">
        <Card :bordered="false" title="通信成功率趋势">
          <EchartsUI ref="trendChartRef" height="300px" />
        </Card>
      </Col>
      <Col :span="10">
        <Card :bordered="false" title="失败原因分布">
          <EchartsUI ref="reasonChartRef" height="300px" />
        </Card>
      </Col>
    </Row>

    <Card :bordered="false" title="通信记录明细">
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
        row-key="date"
        size="middle"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'success_rate'">
            <Tag :color="record.success_rate >= 95 ? 'green' : record.success_rate >= 80 ? 'orange' : 'red'">
              {{ record.success_rate }}%
            </Tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <Tag :color="record.status === 'completed' ? 'green' : 'red'">
              {{ record.status === 'completed' ? '完成' : '失败' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
