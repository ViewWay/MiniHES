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

import { getNonCommDevices } from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const { themedAxis, themedTooltip, watchThemeAndRerender } = useChartTheme();

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const selectedProject = ref<number | undefined>(undefined);
const projectOptions = ref<{ label: string; value: number }[]>([]);
const summary = ref<any>({});
const chartsData = ref<any>({});

const chartRef = ref<EchartsUIType>();
const { renderEcharts: renderBarChart } = useEcharts(chartRef);

const columns = [
  { title: '表号', dataIndex: 'serial_number', width: 150 },
  { title: '表名', dataIndex: 'meter_name', width: 140 },
  { title: '位置', dataIndex: 'location', width: 160 },
  { title: '最后通信', dataIndex: 'last_comm_time', width: 170 },
  { title: '静默时长', key: 'silence', width: 120, dataIndex: 'silence_hours' },
  { title: '在线状态', key: 'online_status', width: 100 },
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
    if (selectedProject.value !== undefined) {
      params.project_id = selectedProject.value;
    }
    const res = await getNonCommDevices(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
    chartsData.value = res.charts || {};
    renderBar();
  } catch {
    message.error('未通信设备数据加载失败');
  } finally {
    loading.value = false;
  }
}

function renderBar() {
  const data = chartsData.value.aging_buckets || { labels: [], series: {} };
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
  selectedProject.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function silenceTagColor(hours: number | null) {
  if (hours === null) return 'default';
  if (hours < 48) return 'gold';
  if (hours < 168) return 'orange';
  return 'red';
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
            <Button type="primary" @click="handleSearch">刷新</Button>
            <Button @click="handleReset">重置</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="未通信总数" :value="summary.total_non_comm" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="24-48小时" :value="summary['24h_48h']" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="2-7天" :value="summary['2d_7d']" :value-style="{ color: '#faad14' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="7-30天" :value="summary['7d_30d']" :value-style="{ color: '#ff7a45' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="30天+" :value="summary['30d_plus']" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="老化分布" style="margin-bottom: 16px">
      <EchartsUI ref="chartRef" height="280px" />
    </Card>

    <Card :bordered="false" title="未通信设备列表">
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
          <template v-if="column.key === 'silence'">
            <Tag :color="silenceTagColor(record.silence_hours)">
              {{ record.silence_label }}
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
