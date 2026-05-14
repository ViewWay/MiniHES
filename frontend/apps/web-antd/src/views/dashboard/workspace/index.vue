<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  message,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'ant-design-vue';

import type { AlarmListParams } from '#/api/modules/alarm';
import {
  getAlarmList,
  getAlarmStats,
  handleAlarm as handleAlarmApi,
  exportAlarms,
} from '#/api/modules/alarm';

// --- Polling ---
const POLL_INTERVAL = 30_000;
let pollTimer: ReturnType<typeof setInterval> | null = null;

// --- State ---
const loading = ref(false);
const alarms = ref<any[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// --- Filter state ---
const filterSeverity = ref<string | undefined>(undefined);
const filterAlarmType = ref<string | undefined>(undefined);
const filterDateRange = ref<[any, any] | null>(null);
const filterHandled = ref<string | undefined>(undefined);

// --- Stats ---
const statsLoading = ref(false);
const statsData = ref<any>({});

const severityMap: Record<string, { color: string; text: string }> = {
  critical: { color: 'red', text: '严重' },
  warning: { color: 'orange', text: '警告' },
  info: { color: 'blue', text: '信息' },
};

const typeMap: Record<string, string> = {
  threshold: '阈值告警',
  anomaly: '数据异常',
  communication: '通信告警',
  stack: '堆栈告警',
  eeprom: 'EEPROM告警',
};

const typeOptions = Object.entries(typeMap).map(([value, label]) => ({
  value,
  label,
}));

const severityOptions = [
  { value: 'critical', label: '严重' },
  { value: 'warning', label: '警告' },
  { value: 'info', label: '信息' },
];

const handledOptions = [
  { value: 'false', label: '未处理' },
  { value: 'true', label: '已处理' },
];

// --- Table columns ---
const columns = [
  { title: '告警ID', dataIndex: 'id', width: 80 },
  { title: '设备', dataIndex: 'meter_name', width: 130, ellipsis: true },
  {
    title: '类型',
    dataIndex: 'alarm_type',
    key: 'alarm_type',
    width: 110,
  },
  { title: '级别', dataIndex: 'severity', key: 'severity', width: 80 },
  { title: '消息', dataIndex: 'alarm_message', ellipsis: true },
  { title: '值', dataIndex: 'alarm_value', width: 100 },
  { title: '阈值', dataIndex: 'threshold_value', width: 100 },
  { title: '时间', dataIndex: 'created_at', width: 170 },
  { title: '状态', dataIndex: 'is_handled', key: 'is_handled', width: 80 },
  { title: '操作', key: 'action', width: 80, fixed: 'right' },
];

// --- Handle alarm modal ---
const handleModalVisible = ref(false);
const handleModalLoading = ref(false);
const currentAlarmId = ref<number | null>(null);
const handleNotes = ref('');

function openHandleModal(id: number) {
  currentAlarmId.value = id;
  handleNotes.value = '';
  handleModalVisible.value = true;
}

function closeHandleModal() {
  handleModalVisible.value = false;
  currentAlarmId.value = null;
  handleNotes.value = '';
}

async function confirmHandleAlarm() {
  if (!currentAlarmId.value) return;
  if (!handleNotes.value.trim()) {
    message.warning('请填写处理说明');
    return;
  }

  handleModalLoading.value = true;
  try {
    await handleAlarmApi(currentAlarmId.value, {
      handle_notes: handleNotes.value.trim(),
    });
    message.success(`告警 #${currentAlarmId.value} 已处理`);
    closeHandleModal();
    await fetchAlarms();
    await fetchStats();
  } catch {
    message.error('操作失败，请重试');
  } finally {
    handleModalLoading.value = false;
  }
}

// --- Computed stats ---
const unhandledCount = computed(
  () =>
    statsData.value?.unhandled_count
    ?? alarms.value.filter((a) => !a.is_handled).length,
);

const criticalCount = computed(
  () =>
    statsData.value?.critical_count
    ?? alarms.value.filter((a) => a.severity === 'critical').length,
);

const warningCount = computed(
  () =>
    statsData.value?.warning_count
    ?? alarms.value.filter((a) => a.severity === 'warning').length,
);

// --- Fetch ---
async function fetchStats() {
  statsLoading.value = true;
  try {
    const res = await getAlarmStats();
    statsData.value = res ?? {};
  } catch {
    statsData.value = {};
  } finally {
    statsLoading.value = false;
  }
}

async function fetchAlarms() {
  loading.value = true;
  try {
    const params: AlarmListParams = {
      page: currentPage.value,
      page_size: pageSize.value,
    };

    if (filterSeverity.value) {
      params.severity = filterSeverity.value;
    }
    if (filterAlarmType.value) {
      params.alarm_type = filterAlarmType.value;
    }
    if (filterHandled.value !== undefined && filterHandled.value !== null) {
      params.is_handled = filterHandled.value === 'true';
    }
    if (filterDateRange.value?.[0]) {
      params.start_date =
        filterDateRange.value[0]?.format?.('YYYY-MM-DD')
        ?? String(filterDateRange.value[0]);
    }
    if (filterDateRange.value?.[1]) {
      params.end_date =
        filterDateRange.value[1]?.format?.('YYYY-MM-DD')
        ?? String(filterDateRange.value[1]);
    }

    const res = await getAlarmList(params);
    alarms.value = res?.items ?? res ?? [];
    total.value = res?.total ?? 0;
  } catch {
    alarms.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function handlePageChange(page: number, size: number) {
  currentPage.value = page;
  pageSize.value = size;
  fetchAlarms();
}

function handleFilter() {
  currentPage.value = 1;
  fetchAlarms();
}

function resetFilter() {
  filterSeverity.value = undefined;
  filterAlarmType.value = undefined;
  filterDateRange.value = null;
  filterHandled.value = undefined;
  currentPage.value = 1;
  fetchAlarms();
}

async function handleExport() {
  try {
    const params: AlarmListParams = {
      page: currentPage.value,
      page_size: pageSize.value,
    };
    if (filterSeverity.value) params.severity = filterSeverity.value;
    if (filterAlarmType.value) params.alarm_type = filterAlarmType.value;
    if (filterHandled.value !== undefined && filterHandled.value !== null) {
      params.is_handled = filterHandled.value === 'true';
    }
    if (filterDateRange.value?.[0]) {
      params.start_date = filterDateRange.value[0]?.format?.('YYYY-MM-DD') ?? String(filterDateRange.value[0]);
    }
    if (filterDateRange.value?.[1]) {
      params.end_date = filterDateRange.value[1]?.format?.('YYYY-MM-DD') ?? String(filterDateRange.value[1]);
    }

    const blob: Blob = await exportAlarms(params);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `告警数据_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败，请重试');
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => {
    fetchAlarms();
    fetchStats();
  }, POLL_INTERVAL);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onMounted(async () => {
  await Promise.allSettled([fetchAlarms(), fetchStats()]);
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <Page auto-content-height>
    <!-- Stats Row -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="6">
        <Card>
          <Statistic title="总告警" :value="total" />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="未处理"
            :value="unhandledCount"
            :value-style="{
              color: (unhandledCount ?? 0) > 0 ? '#ff4d4f' : undefined,
            }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="严重告警"
            :value="criticalCount"
            :value-style="{ color: '#cf1322' }"
          />
        </Card>
      </Col>
      <Col :span="6">
        <Card>
          <Statistic
            title="警告"
            :value="warningCount"
            :value-style="{ color: '#fa8c16' }"
          />
        </Card>
      </Col>
    </Row>

    <!-- Alarm Table -->
    <Card :bordered="false" title="告警管理">
      <template #extra>
        <Space>
          <Button @click="fetchAlarms" :loading="loading">刷新</Button>
          <Button @click="handleExport">导出</Button>
        </Space>
      </template>

      <!-- Filter Bar -->
      <Form layout="inline" style="margin-bottom: 16px">
        <Form.Item label="告警级别">
          <Select
            v-model:value="filterSeverity"
            placeholder="全部"
            :options="severityOptions"
            allow-clear
            style="width: 120px"
            @change="handleFilter"
          />
        </Form.Item>
        <Form.Item label="告警类型">
          <Select
            v-model:value="filterAlarmType"
            placeholder="全部"
            :options="typeOptions"
            allow-clear
            style="width: 140px"
            show-search
            :filter-option="
              (input: string, option: any) =>
                option.label?.toLowerCase().includes(input.toLowerCase())
            "
            @change="handleFilter"
          />
        </Form.Item>
        <Form.Item label="处理状态">
          <Select
            v-model:value="filterHandled"
            placeholder="全部"
            :options="handledOptions"
            allow-clear
            style="width: 120px"
            @change="handleFilter"
          />
        </Form.Item>
        <Form.Item label="日期范围">
          <DatePicker.RangePicker
            v-model:value="filterDateRange"
            style="width: 240px"
            format="YYYY-MM-DD"
            @change="handleFilter"
          />
        </Form.Item>
        <Form.Item>
          <Button @click="resetFilter">重置</Button>
        </Form.Item>
      </Form>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="alarms"
        :loading="loading"
        row-key="id"
        :scroll="{ x: 1300 }"
        :pagination="{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t: number) => `共 ${t} 条`,
          onChange: handlePageChange,
        }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'alarm_type'">
            <Tag>
              {{ typeMap[record.alarm_type] || record.alarm_type }}
            </Tag>
          </template>
          <template v-if="column.key === 'severity'">
            <Tag
              :color="severityMap[record.severity]?.color ?? 'default'"
            >
              {{ severityMap[record.severity]?.text ?? record.severity }}
            </Tag>
          </template>
          <template v-if="column.key === 'is_handled'">
            <Tag :color="record.is_handled ? 'green' : 'orange'">
              {{ record.is_handled ? '已处理' : '未处理' }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Button
              v-if="!record.is_handled"
              type="link"
              size="small"
              @click="openHandleModal(record.id)"
            >
              处理
            </Button>
            <span v-else style="color: #999">-</span>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Handle Alarm Modal -->
    <Modal
      v-model:open="handleModalVisible"
      title="处理告警"
      :confirm-loading="handleModalLoading"
      @ok="confirmHandleAlarm"
      @cancel="closeHandleModal"
    >
      <Form layout="vertical">
        <Form.Item label="处理说明" required>
          <Input.TextArea
            v-model:value="handleNotes"
            placeholder="请输入告警处理说明..."
            :rows="4"
            :maxlength="500"
            show-count
          />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
