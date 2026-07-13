<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import {
  Button, Card, DatePicker, Form, Input, Modal, Select, Space, Table, Tag, Popconfirm, message,
} from 'ant-design-vue';
import type { TableColumnType } from 'ant-design-vue';
import { getMeterList, getBorrowRecords, approveBorrow, createBorrowRequest, returnBorrow } from '#/api/modules/meter';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Filters
const filterStatus = ref<string | undefined>(undefined);

// Create borrow request modal
const showCreateModal = ref(false);
const createLoading = ref(false);
const createForm = ref({
  meter_id: undefined as number | undefined,
  borrower_name: '',
  expected_return_date: '',
  borrow_reason: '',
  department_approver: undefined as number | undefined,
});

// Metadata
const meters = ref<any[]>([]);

const approvalStatusMap: Record<string, { color: string; text: string }> = {
  pending_department: { color: 'orange', text: '待部门审批' },
  pending_lab: { color: 'blue', text: '待实验室审批' },
  approved: { color: 'green', text: '已批准' },
  rejected: { color: 'red', text: '已拒绝' },
  cancelled: { color: 'default', text: '已取消' },
};

const approvalStatusOptions = Object.entries(approvalStatusMap).map(([value, { text }]) => ({ value, label: text }));

const columns: TableColumnType[] = [
  { title: '设备编号', dataIndex: 'meter_serial', width: 130 },
  { title: '设备名称', dataIndex: 'meter_name', width: 150 },
  { title: '借用人', dataIndex: 'borrower_name', width: 100 },
  { title: '借用原因', dataIndex: 'borrow_reason', ellipsis: true },
  { title: '预计归还', dataIndex: 'expected_return_date', key: 'expected_return_date', width: 120 },
  { title: '实际归还', dataIndex: 'actual_return_date', key: 'actual_return_date', width: 120 },
  { title: '部门审批人', dataIndex: 'department_approver_name', key: 'department_approver_name', width: 110 },
  { title: '实验室审批人', dataIndex: 'lab_approver_name', key: 'lab_approver_name', width: 120 },
  { title: '审批状态', dataIndex: 'approval_status', key: 'approval_status', width: 120 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
];

async function fetchMeters() {
  try {
    const res = await getMeterList({ page: 1, page_size: 200 });
    meters.value = res.items || [];
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const res = await getBorrowRecords({ status: filterStatus.value });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function handleFilter() {
  pagination.value.current = 1;
  fetchData();
}

function resetFilter() {
  filterStatus.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return '-';
  return dateStr.slice(0, 10);
}

async function handleApprove(id: number, approved: boolean) {
  try {
    await approveBorrow(id, { approved });
    message.success(approved ? '已批准' : '已拒绝');
    fetchData();
  } catch {
    message.error('操作失败');
  }
}

async function handleReturn(id: number) {
  try {
    await returnBorrow(id);
    message.success('已归还');
    fetchData();
  } catch {
    message.error('归还操作失败');
  }
}

async function handleCreateRequest() {
  createLoading.value = true;
  try {
    await createBorrowRequest(createForm.value as any);
    message.success('借用申请已提交');
    showCreateModal.value = false;
    resetCreateForm();
    fetchData();
  } catch {
    message.error('申请提交失败');
  } finally {
    createLoading.value = false;
  }
}

function resetCreateForm() {
  createForm.value = {
    meter_id: undefined,
    borrower_name: '',
    expected_return_date: '',
    borrow_reason: '',
    department_approver: undefined,
  };
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

onMounted(() => {
  fetchData();
  fetchMeters();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="借用记录管理">
      <template #extra>
        <Button type="primary" @click="showCreateModal = true" style="margin-right: 8px">新建借用申请</Button>
        <Button @click="fetchData">刷新</Button>
      </template>

      <!-- Filters -->
      <Card :bordered="false" style="margin-bottom: 16px">
        <Form layout="inline">
          <Form.Item label="审批状态">
            <Select
              v-model:value="filterStatus"
              placeholder="全部状态"
              allow-clear
              :options="approvalStatusOptions"
              style="width: 160px"
              @change="handleFilter"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" @click="handleFilter">查询</Button>
            <Button style="margin-left: 8px" @click="resetFilter">重置</Button>
          </Form.Item>
        </Form>
      </Card>

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
        :scroll="{ x: 1400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'expected_return_date'">
            {{ formatDate(record.expected_return_date) }}
          </template>
          <template v-if="column.key === 'actual_return_date'">
            {{ formatDate(record.actual_return_date) }}
          </template>
          <template v-if="column.key === 'department_approver_name'">
            {{ record.department_approver_name || '-' }}
          </template>
          <template v-if="column.key === 'lab_approver_name'">
            {{ record.lab_approver_name || '-' }}
          </template>
          <template v-if="column.key === 'approval_status'">
            <Tag :color="approvalStatusMap[record.approval_status]?.color">
              {{ approvalStatusMap[record.approval_status]?.text }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <template v-if="record.approval_status === 'pending_department' || record.approval_status === 'pending_lab'">
                <Popconfirm title="确认批准？" @confirm="handleApprove(record.id, true)">
                  <Button type="link" size="small">批准</Button>
                </Popconfirm>
                <Popconfirm title="确认拒绝？" @confirm="handleApprove(record.id, false)">
                  <Button type="link" size="small" danger>拒绝</Button>
                </Popconfirm>
              </template>
              <template v-if="record.approval_status === 'approved' && !record.actual_return_date">
                <Popconfirm title="确认归还？" @confirm="handleReturn(record.id)">
                  <Button type="link" size="small">归还</Button>
                </Popconfirm>
              </template>
              <span
                v-if="record.approval_status !== 'pending_department'
                  && record.approval_status !== 'pending_lab'
                  && (record.approval_status !== 'approved' || !!record.actual_return_date)"
                style="color: #999"
              >-</span>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Borrow Request Modal -->
    <Modal
      v-model:open="showCreateModal"
      title="新建借用申请"
      :confirm-loading="createLoading"
      @ok="handleCreateRequest"
      width="560px"
    >
      <Form :model="createForm" layout="vertical" style="margin-top: 16px">
        <Form.Item label="选择设备" required>
          <Select
            v-model:value="createForm.meter_id"
            placeholder="请选择要借用的设备"
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
        <Form.Item label="借用人" required>
          <Input v-model:value="createForm.borrower_name" placeholder="请输入借用人姓名" />
        </Form.Item>
        <Form.Item label="预计归还日期" required>
          <DatePicker
            v-model:value="createForm.expected_return_date"
            style="width: 100%"
            value-format="YYYY-MM-DD"
            placeholder="请选择预计归还日期"
          />
        </Form.Item>
        <Form.Item label="借用原因" required>
          <Input.TextArea v-model:value="createForm.borrow_reason" :rows="3" placeholder="请输入借用原因" />
        </Form.Item>
        <Form.Item label="部门审批人ID（可选）">
          <Input v-model:value="createForm.department_approver" type="number" placeholder="可选，指定部门审批人" />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
