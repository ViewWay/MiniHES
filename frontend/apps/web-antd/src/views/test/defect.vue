<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Col, Form, Input, Modal, Row, Select, Space, Table, Tag, message,
} from 'ant-design-vue';
import type { TableColumnType } from 'ant-design-vue';
import { getDefects, addDefect, updateDefect } from '#/api/modules/test';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Filters
const filterSeverity = ref<string | undefined>(undefined);
const filterStatus = ref<string | undefined>(undefined);

// Create modal
const showCreateModal = ref(false);
const createForm = ref({
  title: '',
  description: '',
  severity: 'minor' as string,
  test_task_id: undefined as number | undefined,
  assigned_to: undefined as number | undefined,
});
const createLoading = ref(false);

// Edit modal
const showEditModal = ref(false);
const editForm = ref<any>({});
const editLoading = ref(false);

const severityMap: Record<string, { color: string; text: string }> = {
  critical: { color: 'red', text: '严重' },
  major: { color: 'orange', text: '主要' },
  minor: { color: 'blue', text: '次要' },
};

const statusMap: Record<string, { color: string; text: string }> = {
  open: { color: 'blue', text: '待处理' },
  in_progress: { color: 'orange', text: '处理中' },
  resolved: { color: 'green', text: '已解决' },
  closed: { color: 'default', text: '已关闭' },
};

// Status transition flow: open -> in_progress -> resolved -> closed
const statusTransitions: Record<string, { next: string; label: string; type: 'primary' | 'default' }[]> = {
  open: [{ next: 'in_progress', label: '开始处理', type: 'primary' }],
  in_progress: [{ next: 'resolved', label: '标记已解决', type: 'primary' }],
  resolved: [{ next: 'closed', label: '关闭', type: 'default' }],
  closed: [],
};

const severityOptions = Object.entries(severityMap).map(([value, { text }]) => ({ value, label: text }));
const statusOptions = Object.entries(statusMap).map(([value, { text }]) => ({ value, label: text }));

const columns: TableColumnType[] = [
  { title: '缺陷标题', dataIndex: 'title', width: 200, ellipsis: true },
  { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '指派给', dataIndex: 'assigned_to_name', key: 'assigned_to_name', width: 100 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getDefects({
      severity: filterSeverity.value,
      status: filterStatus.value,
    });
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
  filterSeverity.value = undefined;
  filterStatus.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

async function handleStatusTransition(record: any, nextStatus: string) {
  try {
    await updateDefect(record.id, { status: nextStatus });
    message.success(`状态已更新为「${statusMap[nextStatus]?.text}」`);
    fetchData();
  } catch {
    message.error('状态更新失败');
  }
}

function openEditModal(record: any) {
  editForm.value = { ...record };
  showEditModal.value = true;
}

async function handleEdit() {
  editLoading.value = true;
  try {
    await updateDefect(editForm.value.id, {
      title: editForm.value.title,
      description: editForm.value.description,
      severity: editForm.value.severity,
      assigned_to: editForm.value.assigned_to,
    });
    message.success('缺陷已更新');
    showEditModal.value = false;
    fetchData();
  } catch {
    message.error('更新失败');
  } finally {
    editLoading.value = false;
  }
}

async function handleCreate() {
  if (!createForm.value.test_task_id) {
    message.warning('请输入测试任务ID');
    return;
  }
  createLoading.value = true;
  try {
    await addDefect(createForm.value.test_task_id, createForm.value as any);
    message.success('缺陷已创建');
    showCreateModal.value = false;
    resetCreateForm();
    fetchData();
  } catch {
    message.error('创建失败');
  } finally {
    createLoading.value = false;
  }
}

function resetCreateForm() {
  createForm.value = {
    title: '',
    description: '',
    severity: 'minor',
    test_task_id: undefined,
    assigned_to: undefined,
  };
}

onMounted(() => { fetchData(); });
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="缺陷管理">
      <template #extra>
        <Button type="primary" @click="showCreateModal = true" style="margin-right: 8px">新增缺陷</Button>
        <Button @click="fetchData">刷新</Button>
      </template>

      <!-- Filters -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Select
            v-model:value="filterSeverity"
            placeholder="严重程度"
            allow-clear
            :options="severityOptions"
            style="width: 100%"
            @change="handleFilter"
          />
        </Col>
        <Col :span="6">
          <Select
            v-model:value="filterStatus"
            placeholder="状态"
            allow-clear
            :options="statusOptions"
            style="width: 100%"
            @change="handleFilter"
          />
        </Col>
        <Col :span="6">
          <Button @click="resetFilter">重置</Button>
        </Col>
      </Row>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        row-key="id"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total }"
        @change="(pag: any) => { pagination.current = pag.current; pagination.pageSize = pag.pageSize; fetchData(); }"
        :scroll="{ x: 1100 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <Tag :color="severityMap[record.severity]?.color">
              {{ severityMap[record.severity]?.text }}
            </Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="statusMap[record.status]?.color">
              {{ statusMap[record.status]?.text }}
            </Tag>
          </template>
          <template v-if="column.key === 'assigned_to_name'">
            {{ record.assigned_to_name || '-' }}
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <template v-for="transition in statusTransitions[record.status] || []" :key="transition.next">
                <Button
                  :type="transition.type"
                  size="small"
                  @click="handleStatusTransition(record, transition.next)"
                >
                  {{ transition.label }}
                </Button>
              </template>
              <Button type="link" size="small" @click="openEditModal(record)">编辑</Button>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Defect Modal -->
    <Modal
      v-model:open="showCreateModal"
      title="新增缺陷"
      :confirm-loading="createLoading"
      @ok="handleCreate"
      width="520px"
    >
      <Form :model="createForm" layout="vertical" style="margin-top: 16px">
        <Form.Item label="测试任务ID" required>
          <Input v-model:value="createForm.test_task_id" type="number" placeholder="请输入关联的测试任务ID" />
        </Form.Item>
        <Form.Item label="标题" required>
          <Input v-model:value="createForm.title" placeholder="请输入缺陷标题" />
        </Form.Item>
        <Form.Item label="严重程度">
          <Select v-model:value="createForm.severity" :options="severityOptions" />
        </Form.Item>
        <Form.Item label="指派给">
          <Input v-model:value="createForm.assigned_to" type="number" placeholder="用户ID（可选）" />
        </Form.Item>
        <Form.Item label="描述">
          <Input.TextArea v-model:value="createForm.description" :rows="4" placeholder="请描述缺陷详情" />
        </Form.Item>
      </Form>
    </Modal>

    <!-- Edit Defect Modal -->
    <Modal
      v-model:open="showEditModal"
      title="编辑缺陷"
      :confirm-loading="editLoading"
      @ok="handleEdit"
      width="520px"
    >
      <Form :model="editForm" layout="vertical" style="margin-top: 16px">
        <Form.Item label="标题" required>
          <Input v-model:value="editForm.title" />
        </Form.Item>
        <Form.Item label="严重程度">
          <Select v-model:value="editForm.severity" :options="severityOptions" />
        </Form.Item>
        <Form.Item label="指派给">
          <Input v-model:value="editForm.assigned_to" type="number" placeholder="用户ID（可选）" />
        </Form.Item>
        <Form.Item label="描述">
          <Input.TextArea v-model:value="editForm.description" :rows="4" />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
