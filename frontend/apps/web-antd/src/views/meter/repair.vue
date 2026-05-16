<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Col, DatePicker, Form, Input, InputNumber, Modal, Row, Select, Statistic, Table, Tag, message,
} from 'ant-design-vue';
import type { TableColumnType } from 'ant-design-vue';
import { getMeterList, getRepairRecords, addRepairRecord } from '#/api/modules/meter';
import { DEFAULT_PAGE_SIZE, METADATA_FETCH_SIZE, THEME_COLORS } from '#/constants';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: DEFAULT_PAGE_SIZE });

// Filters
const filterStatus = ref<string | undefined>(undefined);
const dateRange = ref<[string, string] | null>(null);

// Create modal
const showCreateModal = ref(false);
const createLoading = ref(false);
const createForm = ref({
  meter_id: undefined as number | undefined,
  description: '',
  cost: undefined as number | undefined,
});

// Metadata
const meters = ref<any[]>([]);

const repairStatusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'orange', text: '待维修' },
  in_progress: { color: 'blue', text: '维修中' },
  completed: { color: 'green', text: '已完成' },
};

const repairStatusOptions = Object.entries(repairStatusMap).map(([value, { text }]) => ({ value, label: text }));

const columns: TableColumnType[] = [
  { title: '设备编号', dataIndex: 'meter_serial', width: 130 },
  { title: '设备名称', dataIndex: 'meter_name', width: 150 },
  { title: '维修描述', dataIndex: 'description', ellipsis: true },
  { title: '维修费用', dataIndex: 'cost', key: 'cost', width: 110 },
  { title: '维修状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '维修时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作人', dataIndex: 'operator_name', width: 100 },
];

// Computed statistics
const totalCost = computed(() => {
  return tableData.value.reduce((sum: number, r: any) => sum + (r.cost || 0), 0);
});

const pendingCount = computed(() => {
  return tableData.value.filter((r: any) => r.status === 'pending').length;
});

const inProgressCount = computed(() => {
  return tableData.value.filter((r: any) => r.status === 'in_progress').length;
});

const completedCount = computed(() => {
  return tableData.value.filter((r: any) => r.status === 'completed').length;
});

async function fetchMeters() {
  try {
    const res = await getMeterList({ page: 1, page_size: METADATA_FETCH_SIZE });
    meters.value = res.items || [];
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      status: filterStatus.value,
    };
    if (dateRange.value) {
      params.start_date = dateRange.value[0];
      params.end_date = dateRange.value[1];
    }
    const res = await getRepairRecords(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } catch {
    message.error('获取维修记录失败');
  } finally {
    loading.value = false;
  }
}

function handleFilter() {
  fetchData();
}

function resetFilter() {
  filterStatus.value = undefined;
  dateRange.value = null;
  fetchData();
}

function handleDateRangeChange(dates: any) {
  if (dates && dates.length === 2) {
    dateRange.value = [dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')];
  } else {
    dateRange.value = null;
  }
  fetchData();
}

async function handleCreate() {
  if (!createForm.value.meter_id) {
    message.warning('请选择设备');
    return;
  }
  createLoading.value = true;
  try {
    await addRepairRecord(createForm.value as any);
    message.success('维修记录已添加');
    showCreateModal.value = false;
    resetCreateForm();
    fetchData();
  } catch {
    message.error('添加失败');
  } finally {
    createLoading.value = false;
  }
}

function resetCreateForm() {
  createForm.value = {
    meter_id: undefined,
    description: '',
    cost: undefined,
  };
}

onMounted(() => {
  fetchData();
  fetchMeters();
});

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="维修记录">
      <template #extra>
        <Button type="primary" @click="showCreateModal = true" style="margin-right: 8px">添加记录</Button>
        <Button @click="fetchData">刷新</Button>
      </template>

      <!-- Statistics Summary -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Card size="small">
            <Statistic title="维修总费用" :value="totalCost" prefix="¥" :precision="2" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="待维修" :value="pendingCount" :value-style="{ color: THEME_COLORS.ORANGE }" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="维修中" :value="inProgressCount" :value-style="{ color: THEME_COLORS.PROCESSING }" />
          </Card>
        </Col>
        <Col :span="6">
          <Card size="small">
            <Statistic title="已完成" :value="completedCount" :value-style="{ color: THEME_COLORS.SUCCESS }" />
          </Card>
        </Col>
      </Row>

      <!-- Filters -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Select
            v-model:value="filterStatus"
            placeholder="维修状态"
            allow-clear
            :options="repairStatusOptions"
            style="width: 100%"
            @change="handleFilter"
          />
        </Col>
        <Col :span="8">
          <DatePicker.RangePicker
            style="width: 100%"
            :placeholder="['开始日期', '结束日期']"
            @change="handleDateRangeChange"
          />
        </Col>
        <Col :span="4">
          <Button @click="resetFilter">重置</Button>
        </Col>
      </Row>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total,
          showSizeChanger: true,
        }"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'cost'">
            {{ record.cost != null ? `¥${Number(record.cost).toFixed(2)}` : '-' }}
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="repairStatusMap[record.status]?.color">
              {{ repairStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? record.created_at.slice(0, 16).replace('T', ' ') : '-' }}
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Repair Record Modal -->
    <Modal
      v-model:open="showCreateModal"
      title="添加维修记录"
      :confirm-loading="createLoading"
      @ok="handleCreate"
      width="520px"
    >
      <Form :model="createForm" layout="vertical" style="margin-top: 16px">
        <Form.Item label="选择设备" required>
          <Select
            v-model:value="createForm.meter_id"
            placeholder="请选择设备"
            show-search
            :filter-option="(input: string, option: any) => option.label?.toLowerCase().includes(input.toLowerCase())"
          >
            <Select.Option
              v-for="m in meters"
              :key="m.id"
              :value="m.id"
              :label="`${m.serial_number} - ${m.meter_name}`"
            >
              {{ m.serial_number }} - {{ m.meter_name }}
            </Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="维修描述" required>
          <Input.TextArea v-model:value="createForm.description" :rows="4" placeholder="请描述维修内容" />
        </Form.Item>
        <Form.Item label="维修费用">
          <InputNumber v-model:value="createForm.cost" style="width: 100%" prefix="¥" :min="0" :precision="2" />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
