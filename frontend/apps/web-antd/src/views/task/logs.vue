<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Badge, Button, Card, DatePicker, Descriptions, DescriptionsItem, Modal, Space, Table, Tag, Tooltip, message } from 'ant-design-vue';
import { getTaskLogs, getTaskDeviceLog } from '#/api/modules/task';
import { DEFAULT_PAGE_SIZE, POLL_INTERVALS } from '#/constants';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: DEFAULT_PAGE_SIZE });

// Auto-refresh state
let pollingTimer: ReturnType<typeof setInterval> | null = null;
const autoRefreshEnabled = ref(true);

// Device detail modal
const detailModalVisible = ref(false);
const detailLoading = ref(false);
const detailLogId = ref<number>(0);
const deviceDetails = ref<any[]>([]);
const detailColumns = [
  { title: '设备编号', dataIndex: 'serial_number', width: 130 },
  { title: '设备名称', dataIndex: 'meter_name', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '耗时(ms)', dataIndex: 'duration_ms', width: 100 },
  { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
];

// Date range filter
const dateRange = ref<[string, string] | null>(null);

const logStatusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  running: { color: 'blue', text: '执行中' },
  completed: { color: 'green', text: '已完成' },
  failed: { color: 'red', text: '失败' },
};

const taskId = computed(() => Number(route.query.task_id) || 0);

const columns = [
  { title: '开始时间', dataIndex: 'start_time', width: 170, sorter: true },
  { title: '结束时间', dataIndex: 'end_time', width: 170 },
  { title: '耗时', dataIndex: 'duration_ms', key: 'duration_ms', width: 100, align: 'center' as const },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center' as const },
  { title: '总设备', dataIndex: 'total_devices', width: 80, align: 'center' as const },
  { title: '成功', dataIndex: 'success_devices', width: 80, align: 'center' as const },
  { title: '失败', dataIndex: 'failed_devices', width: 80, align: 'center' as const },
  { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
  { title: '详情', key: 'detail', width: 80, align: 'center' as const },
];

async function fetchData() {
  if (!taskId.value) return;
  loading.value = true;
  try {
    const params: any = {
      task_id: taskId.value,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (dateRange.value) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }
    const res = await getTaskLogs(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

async function fetchDeviceDetails(logId: number) {
  detailLogId.value = logId;
  detailModalVisible.value = true;
  detailLoading.value = true;
  try {
    const res = await getTaskDeviceLog(logId);
    deviceDetails.value = res.items || res || [];
  } catch {
    deviceDetails.value = [];
  } finally {
    detailLoading.value = false;
  }
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function startPolling() {
  stopPolling();
  if (autoRefreshEnabled.value) {
    pollingTimer = setInterval(() => {
      fetchData();
    }, POLL_INTERVALS.TASK_LOGS);
  }
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
  if (autoRefreshEnabled.value) {
    startPolling();
    message.success('已开启自动刷新（10秒间隔）');
  } else {
    stopPolling();
    message.info('已关闭自动刷新');
  }
}

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function handleDateRangeChange(dates: any) {
  if (dates && dates.length === 2) {
    dateRange.value = [dates[0]?.format('YYYY-MM-DD'), dates[1]?.format('YYYY-MM-DD')];
  } else {
    dateRange.value = null;
  }
}

onMounted(() => {
  fetchData();
  startPolling();
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

onUnmounted(() => {
  stopPolling();
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});

function handleVisibilityChange() {
  if (document.hidden) {
    stopPolling();
  } else {
    startPolling();
  }
}
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="任务执行日志">
      <template #extra>
        <Space>
          <Button @click="toggleAutoRefresh" :type="autoRefreshEnabled ? 'primary' : 'default'" size="small">
            {{ autoRefreshEnabled ? '自动刷新: 开' : '自动刷新: 关' }}
          </Button>
          <Button @click="fetchData">手动刷新</Button>
          <Button @click="router.push('/task/list')">返回任务列表</Button>
        </Space>
      </template>

      <!-- Filter bar -->
      <Card size="small" style="margin-bottom: 16px">
        <Space>
          <span>日期范围:</span>
          <DatePicker.RangePicker
            style="width: 260px"
            :placeholder="['开始日期', '结束日期']"
            @change="handleDateRangeChange"
          />
          <Button type="primary" @click="() => { pagination.current = 1; fetchData(); }">查询</Button>
        </Space>
      </Card>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id"
        @change="handleTableChange"
        :scroll="{ x: 1100 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Badge :status="record.status === 'running' ? 'processing' : record.status === 'completed' ? 'success' : record.status === 'failed' ? 'error' : 'default'" />
            <Tag :color="logStatusMap[record.status]?.color" style="margin-left: 4px">
              {{ logStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'duration_ms'">
            {{ formatDuration(record.duration_ms) }}
          </template>
          <template v-if="column.key === 'error_message'">
            <Tooltip v-if="record.error_message" :title="record.error_message">
              <span style="color: #ff4d4f; cursor: pointer">{{ record.error_message }}</span>
            </Tooltip>
            <span v-else style="color: #999">-</span>
          </template>
          <template v-if="column.key === 'detail'">
            <Button type="link" size="small" @click="fetchDeviceDetails(record.id)">
              查看
            </Button>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Device execution detail modal -->
    <Modal
      v-model:open="detailModalVisible"
      title="设备执行详情"
      width="900px"
      :footer="null"
      destroy-on-close
    >
      <Descriptions bordered :column="3" size="small" style="margin-bottom: 16px">
        <DescriptionsItem label="日志ID">{{ detailLogId }}</DescriptionsItem>
        <DescriptionsItem label="设备总数">{{ deviceDetails.length }}</DescriptionsItem>
        <DescriptionsItem label="失败数">{{ deviceDetails.filter((d: any) => d.status === 'failed').length }}</DescriptionsItem>
      </Descriptions>
      <Table
        :columns="detailColumns"
        :data-source="deviceDetails"
        :loading="detailLoading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="logStatusMap[record.status]?.color">
              {{ logStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
        </template>
      </Table>
    </Modal>
  </Page>
</template>
