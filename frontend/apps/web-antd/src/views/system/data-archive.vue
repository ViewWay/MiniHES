<script lang="ts" setup>
import { onMounted, ref, computed } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  Form,
  FormItem,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  message,
} from 'ant-design-vue';

import { getArchiveRecords, createArchive } from '#/api/modules/system';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Modal state
const showModal = ref(false);
const submitting = ref(false);
const formState = ref({
  archive_type: 'postgresql' as string,
  table_name: 'col_task_log' as string,
  days_to_archive: 90 as number,
});

const archiveTypeOptions = [
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'InfluxDB', value: 'influxdb' },
];

const tableNameOptions = [
  { label: '采集任务日志 (col_task_log)', value: 'col_task_log' },
  { label: '数据质量统计 (col_data_quality)', value: 'col_data_quality' },
];

// Summary stats (computed from table data or API response)
const summaryStats = computed(() => {
  const items = tableData.value;
  const pgCount = items.filter(
    (i: any) => i.archive_type === 'postgresql',
  ).length;
  const influxCount = items.filter(
    (i: any) => i.archive_type === 'influxdb',
  ).length;
  const totalRecords = items.reduce(
    (sum: number, i: any) => sum + (i.record_count || 0),
    0,
  );
  return {
    total: total.value,
    pgCount,
    influxCount,
    totalRecords,
  };
});

const columns = [
  {
    title: '归档类型',
    dataIndex: 'archive_type',
    key: 'archive_type',
    width: 130,
  },
  { title: '表名', dataIndex: 'table_name', width: 160 },
  { title: '开始时间', dataIndex: 'start_time', width: 170 },
  { title: '结束时间', dataIndex: 'end_time', width: 170 },
  { title: '记录数', dataIndex: 'record_count', width: 100 },
  {
    title: '状态',
    dataIndex: 'archive_status',
    key: 'archive_status',
    width: 100,
  },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
];

const statusColorMap: Record<string, string> = {
  completed: 'green',
  running: 'blue',
  failed: 'red',
  pending: 'default',
};

const statusTextMap: Record<string, string> = {
  completed: '已完成',
  running: '进行中',
  failed: '失败',
  pending: '待执行',
};

async function fetchData() {
  loading.value = true;
  try {
    const res = await getArchiveRecords({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function openCreateModal() {
  formState.value = {
    archive_type: 'postgresql',
    table_name: 'col_task_log',
    days_to_archive: 90,
  };
  showModal.value = true;
}

async function handleSubmit() {
  if (!formState.value.days_to_archive || formState.value.days_to_archive <= 0) {
    message.warning('请输入有效的归档天数');
    return;
  }
  submitting.value = true;
  try {
    await createArchive({
      archive_type: formState.value.archive_type,
      table_name: formState.value.table_name,
      days_to_archive: formState.value.days_to_archive,
    });
    message.success('归档任务已创建');
    showModal.value = false;
    fetchData();
  } catch {
    message.error('创建归档任务失败');
  } finally {
    submitting.value = false;
  }
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <Page auto-content-height>
    <!-- Summary cards -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="总归档数" :value="summaryStats.total" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="PostgreSQL 归档"
            :value="summaryStats.pgCount"
            :value-style="{ color: '#336791' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="InfluxDB 归档"
            :value="summaryStats.influxCount"
            :value-style="{ color: '#5951de' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="总归档记录数"
            :value="summaryStats.totalRecords"
          />
        </Card>
      </Col>
    </Row>

    <!-- Table -->
    <Card :bordered="false" title="数据归档管理">
      <template #extra>
        <Space>
          <Button type="primary" @click="openCreateModal">手动归档</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>
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
        @change="handleTableChange"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'archive_type'">
            <Tag :color="record.archive_type === 'postgresql' ? '#336791' : '#5951de'">
              {{ record.archive_type === 'postgresql' ? 'PostgreSQL' : 'InfluxDB' }}
            </Tag>
          </template>
          <template v-if="column.key === 'archive_status'">
            <Tag :color="statusColorMap[record.archive_status] || 'default'">
              {{ statusTextMap[record.archive_status] || record.archive_status }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create archive modal -->
    <Modal
      v-model:open="showModal"
      title="手动归档"
      :confirm-loading="submitting"
      @ok="handleSubmit"
      width="520px"
    >
      <Form :model="formState" layout="vertical" style="margin-top: 16px">
        <FormItem label="归档类型" required>
          <Select
            v-model:value="formState.archive_type"
            :options="archiveTypeOptions"
          />
        </FormItem>
        <FormItem label="目标表" required>
          <Select
            v-model:value="formState.table_name"
            :options="tableNameOptions"
          />
        </FormItem>
        <FormItem label="归档天数" required>
          <InputNumber
            v-model:value="formState.days_to_archive"
            :min="1"
            :max="3650"
            style="width: 100%"
            placeholder="归档多少天前的数据"
            addon-after="天"
          />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
