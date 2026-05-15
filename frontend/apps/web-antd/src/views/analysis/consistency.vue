<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { computed, onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  Form,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  message,
} from 'ant-design-vue';

import {
  getConsistencyCheck,
  triggerConsistencyCheck,
} from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';

const loading = ref(false);
const checking = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// Filters
const projectOptions = ref<{ label: string; value: number }[]>([]);
const selectedProject = ref<number | undefined>(undefined);

// Summary
const summary = computed(() => {
  const items = tableData.value;
  if (!items.length) return null;
  const checked = items.length;
  const consistent = items.filter(
    (i: any) => i.missing_days === 0,
  ).length;
  const inconsistent = items.filter(
    (i: any) => i.missing_days != null && i.missing_days > 0,
  ).length;
  const missingData = items.filter(
    (i: any) => i.pg_task_days == null || i.influxdb_data_days == null,
  ).length;
  return { checked, consistent, inconsistent, missingData };
});

// Chart ref
const pieChartRef = ref<EchartsUIType>();
const { renderEcharts: renderPieChart } = useEcharts(pieChartRef);

// Table columns
const columns = [
  { title: '出厂编号', dataIndex: 'serial_number', width: 150 },
  { title: '设备名称', dataIndex: 'device_name', width: 140 },
  { title: '项目', dataIndex: 'project_name', width: 130 },
  { title: 'PG任务天数', dataIndex: 'pg_task_days', width: 120, align: 'center' as const },
  { title: 'InfluxDB数据天数', dataIndex: 'influxdb_data_days', width: 150, align: 'center' as const },
  { title: '缺失天数', dataIndex: 'missing_days', key: 'missing_days', width: 110, align: 'center' as const },
  { title: '最后检查时间', dataIndex: 'last_check_time', width: 180 },
];

function getMissingDaysColor(missingDays: number | null | undefined): string {
  if (missingDays == null) return 'default';
  if (missingDays === 0) return 'green';
  if (missingDays <= 2) return 'orange';
  return 'red';
}

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
    const res = await getConsistencyCheck({
      project_id: selectedProject.value,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
    renderCharts();
  } finally {
    loading.value = false;
  }
}

async function handleCheck() {
  checking.value = true;
  try {
    await triggerConsistencyCheck();
    message.success('一致性检查已触发，正在重新查询结果');
    await fetchData();
  } catch {
    message.error('检查触发失败');
  } finally {
    checking.value = false;
  }
}

function renderCharts() {
  const items = tableData.value;
  if (!items.length) return;

  const consistent = items.filter((i: any) => i.missing_days === 0).length;
  const inconsistent = items.filter(
    (i: any) => i.missing_days != null && i.missing_days > 0,
  ).length;
  const missingData = items.filter(
    (i: any) => i.pg_task_days == null || i.influxdb_data_days == null,
  ).length;

  renderPieChart({
    title: {
      text: '一致性分布',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: 0,
      data: ['一致', '不一致', '数据缺失'],
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: '{b}: {c}',
        },
        data: [
          { value: consistent, name: '一致', itemStyle: { color: '#52c41a' } },
          { value: inconsistent, name: '不一致', itemStyle: { color: '#faad14' } },
          { value: missingData, name: '数据缺失', itemStyle: { color: '#ff4d4f' } },
        ].filter((d) => d.value > 0),
      },
    ],
  });
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
    <!-- Action bar -->
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
        <Form.Item>
          <Space>
            <Button type="primary" @click="fetchData" :loading="loading">
              查询
            </Button>
            <Button @click="fetchData">刷新</Button>
            <Button type="primary" danger @click="handleCheck" :loading="checking">
              执行检查
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <!-- Summary cards -->
    <Row v-if="summary" :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="已检查设备" :value="summary.checked" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="数据一致"
            :value="summary.consistent"
            :value-style="{ color: '#52c41a' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="数据不一致"
            :value="summary.inconsistent"
            :value-style="{ color: '#faad14' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="数据缺失"
            :value="summary.missingData"
            :value-style="{ color: '#ff4d4f' }"
          />
        </Card>
      </Col>
    </Row>

    <!-- Pie chart -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="24">
        <Card :bordered="false" title="一致性分布">
          <EchartsUI ref="pieChartRef" height="300px" />
        </Card>
      </Col>
    </Row>

    <!-- Data table -->
    <Card :bordered="false" title="一致性检查结果">
      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        row-key="serial_number"
        :pagination="{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t: number) => `共 ${t} 条`,
          onChange: handlePageChange,
        }"
        :scroll="{ x: 1000 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'missing_days'">
            <Tag :color="getMissingDaysColor(record.missing_days)">
              {{ record.missing_days ?? '-' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>