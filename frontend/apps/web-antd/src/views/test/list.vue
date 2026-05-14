<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Col, Form, Input, InputNumber, Modal, Row, Select, Space, Table, Tag, message,
} from 'ant-design-vue';
import type { TableColumnType } from 'ant-design-vue';
import { getTestList, createTestTask } from '#/api/modules/test';
import { getProjectList } from '#/api/modules/project';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Filter state
const filterType = ref<string | undefined>(undefined);
const filterStatus = ref<string | undefined>(undefined);
const filterProject = ref<number | undefined>(undefined);

// Create task modal
const showCreateModal = ref(false);
const createForm = ref({
  test_type: 'protocol' as string,
  project_id: undefined as number | undefined,
  device_count: 1 as number,
  description: '',
});
const createLoading = ref(false);

// Metadata
const projects = ref<any[]>([]);

const testTypeMap: Record<string, { color: string; text: string }> = {
  protocol: { color: 'blue', text: '协议测试' },
  accuracy: { color: 'green', text: '采集准确性' },
  function: { color: 'purple', text: '功能测试' },
  stability: { color: 'orange', text: '稳定性测试' },
};

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  running: { color: 'blue', text: '执行中' },
  completed: { color: 'green', text: '已完成' },
  failed: { color: 'red', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
};

const testTypeOptions = Object.entries(testTypeMap).map(([value, { text }]) => ({ value, label: text }));
const statusOptions = Object.entries(statusMap).map(([value, { text }]) => ({ value, label: text }));

const columns: TableColumnType[] = [
  { title: '测试编号', dataIndex: 'id', width: 80 },
  { title: '测试类型', dataIndex: 'test_type', key: 'test_type', width: 120 },
  { title: '项目', dataIndex: 'project_name', width: 120 },
  { title: '设备数', dataIndex: 'device_count', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '测试时长', dataIndex: 'duration', key: 'duration', width: 110 },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
];

async function fetchProjects() {
  try {
    const res = await getProjectList();
    projects.value = res.items || res || [];
  } catch { /* ignore */ }
}

async function fetchData() {
  loading.value = true;
  try {
    const res = await getTestList({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      test_type: filterType.value,
      status: filterStatus.value,
      project_id: filterProject.value,
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
  filterType.value = undefined;
  filterStatus.value = undefined;
  filterProject.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function formatDuration(record: any) {
  if (!record.started_at) return '-';
  const start = new Date(record.started_at).getTime();
  const end = record.completed_at ? new Date(record.completed_at).getTime() : Date.now();
  const diff = Math.floor((end - start) / 1000);
  if (diff < 60) return `${diff}秒`;
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时`;
  return `${Math.floor(diff / 86400)}天`;
}

async function handleCreateTask() {
  createLoading.value = true;
  try {
    await createTestTask(createForm.value as any);
    message.success('测试任务已创建');
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
    test_type: 'protocol',
    project_id: undefined,
    device_count: 1,
    description: '',
  };
}

onMounted(() => {
  fetchData();
  fetchProjects();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="测试列表">
      <template #extra>
        <Button type="primary" @click="showCreateModal = true" style="margin-right: 8px">创建测试任务</Button>
        <Button @click="fetchData">刷新</Button>
      </template>

      <!-- Filters -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Select
            v-model:value="filterType"
            placeholder="测试类型"
            allow-clear
            :options="testTypeOptions"
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
          <Select
            v-model:value="filterProject"
            placeholder="所属项目"
            allow-clear
            style="width: 100%"
            @change="handleFilter"
          >
            <Select.Option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</Select.Option>
          </Select>
        </Col>
        <Col :span="6">
          <Button @click="resetFilter">重置</Button>
        </Col>
      </Row>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total }"
        row-key="id"
        @change="handleTableChange"
        :scroll="{ x: 1000 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'test_type'">
            <Tag :color="testTypeMap[record.test_type]?.color">
              {{ testTypeMap[record.test_type]?.text || record.test_type }}
            </Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="statusMap[record.status]?.color">
              {{ statusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'duration'">
            {{ formatDuration(record) }}
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="router.push(`/test/report/${record.id}`)">报告</Button>
              <Button type="link" size="small" @click="router.push('/test/defect')">缺陷</Button>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Create Test Task Modal -->
    <Modal
      v-model:open="showCreateModal"
      title="创建测试任务"
      :confirm-loading="createLoading"
      @ok="handleCreateTask"
      width="520px"
    >
      <Form :model="createForm" layout="vertical" style="margin-top: 16px">
        <Form.Item label="测试类型" required>
          <Select v-model:value="createForm.test_type" :options="testTypeOptions" />
        </Form.Item>
        <Form.Item label="所属项目" required>
          <Select v-model:value="createForm.project_id" placeholder="请选择项目">
            <Select.Option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="设备数量">
          <InputNumber v-model:value="createForm.device_count" :min="1" style="width: 100%" />
        </Form.Item>
        <Form.Item label="备注">
          <Input.TextArea v-model:value="createForm.description" :rows="3" placeholder="可选描述" />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
