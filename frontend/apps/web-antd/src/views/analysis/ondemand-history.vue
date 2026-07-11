<script lang="ts" setup>

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

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

import { getOndemandHistory } from '#/api/modules/analysis';

const RangePicker = DatePicker.RangePicker;

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const dateRange = ref<any>(null);
const summary = ref<any>({});

const columns = [
  { title: '任务名称', dataIndex: 'task_name', width: 180 },
  { title: '开始时间', dataIndex: 'start_time', width: 170 },
  { title: '结束时间', dataIndex: 'end_time', width: 170 },
  { title: '耗时(ms)', dataIndex: 'duration_ms', width: 100 },
  { title: '总设备', dataIndex: 'total_devices', width: 90 },
  { title: '成功', dataIndex: 'success_devices', width: 80 },
  { title: '失败', dataIndex: 'failed_devices', width: 80 },
  { title: '状态', key: 'status', width: 100, dataIndex: 'status' },
  { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
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
    const res = await getOndemandHistory(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    summary.value = res.summary || {};
  } catch {
    message.error('按需抄表历史数据加载失败');
  } finally {
    loading.value = false;
  }
}

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
          <Statistic title="总抄表次数" :value="summary.total_reads" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="成功" :value="summary.success" :value-style="{ color: '#52c41a' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="失败" :value="summary.failed" :value-style="{ color: '#ff4d4f' }" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic title="成功率" :value="summary.success_rate" suffix="%" />
        </Card>
      </Col>
    </Row>

    <Card v-if="summary.demo" :bordered="false" style="margin-bottom: 16px" :body-style="{ padding: '8px 16px' }">
      <Tag color="orange">无数据</Tag>
      <span style="margin-left: 8px; color: #999; font-size: 12px">当前查询范围内无采集数据</span>
    </Card>

    <Card :bordered="false" title="按需抄表历史">
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
            <Tag :color="record.status === 'completed' ? 'green' : record.status === 'running' ? 'blue' : 'red'">
              {{ record.status === 'completed' ? '完成' : record.status === 'running' ? '运行中' : '失败' }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
