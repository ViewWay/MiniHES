<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Button, Card, Col, DatePicker, Form, Input, Row, Select, Space, Switch, Table, Tag, Popconfirm, message } from 'ant-design-vue';
import { getTaskList, executeTask, toggleTask, deleteTask } from '#/api/modules/task';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Search and filter state
const searchKeyword = ref('');
const filterStatus = ref<string | undefined>(undefined);
const filterTaskType = ref<string | undefined>(undefined);

const taskStatusMap: Record<string, { color: string; text: string }> = {
  ready: { color: 'default', text: '就绪' },
  running: { color: 'blue', text: '执行中' },
  paused: { color: 'orange', text: '已暂停' },
  completed: { color: 'green', text: '已完成' },
  failed: { color: 'red', text: '失败' },
};

const taskTypeMap: Record<string, string> = { cron: '定时任务', interval: '循环任务', once: '一次性任务' };

const statusFilterOptions = [
  { value: 'ready', label: '就绪' },
  { value: 'running', label: '执行中' },
  { value: 'paused', label: '已暂停' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
];

const taskTypeFilterOptions = [
  { value: 'cron', label: '定时任务' },
  { value: 'interval', label: '循环任务' },
  { value: 'once', label: '一次性任务' },
];

const columns = [
  { title: '任务名称', dataIndex: 'task_name', width: 200, ellipsis: true },
  { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 110 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '设备数', dataIndex: 'total_devices', width: 80, align: 'center' as const },
  { title: '成功率', dataIndex: 'success_rate', key: 'success_rate', width: 90, align: 'center' as const },
  { title: '最后执行', dataIndex: 'last_execute_time', width: 170 },
  { title: '下次执行', dataIndex: 'next_execute_time', width: 170 },
  { title: '启用', dataIndex: 'is_enabled', key: 'is_enabled', width: 70, align: 'center' as const },
  { title: '操作', key: 'action', width: 220, fixed: 'right' as const },
];

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    if (filterStatus.value) params.status = filterStatus.value;
    if (filterTaskType.value) params.task_type = filterTaskType.value;
    const res = await getTaskList(params as any);
    let items = res.items || [];
    // Client-side keyword filter
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase();
      items = items.filter((t: any) => t.task_name?.toLowerCase().includes(kw));
    }
    tableData.value = items;
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleReset() {
  searchKeyword.value = '';
  filterStatus.value = undefined;
  filterTaskType.value = undefined;
  pagination.value.current = 1;
  fetchData();
}

async function handleExecute(id: number) {
  try {
    await executeTask(id);
    message.success('任务已触发执行');
    fetchData();
  } catch {
    message.error('执行失败');
  }
}

async function handleToggle(id: number, enabled: boolean) {
  try {
    await toggleTask(id, enabled);
    message.success(enabled ? '已启用' : '已禁用');
    fetchData();
  } catch {
    message.error('操作失败');
  }
}

async function handleDelete(id: number) {
  try {
    await deleteTask(id);
    message.success('已删除');
    fetchData();
  } catch {
    message.error('删除失败');
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
    <Card :bordered="false" title="采集任务列表">
      <template #extra>
        <Space>
          <Button type="primary" v-access:code="'task:create'" @click="router.push('/task/create')">创建任务</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>

      <!-- Search & Filter Bar -->
      <Card size="small" style="margin-bottom: 16px">
        <Form layout="inline">
          <Form.Item label="关键词">
            <Input
              v-model:value="searchKeyword"
              placeholder="搜索任务名称"
              allow-clear
              style="width: 200px"
              @press-enter="handleSearch"
            />
          </Form.Item>
          <Form.Item label="状态">
            <Select
              v-model:value="filterStatus"
              :options="statusFilterOptions"
              allow-clear
              placeholder="全部状态"
              style="width: 140px"
              @change="handleSearch"
            />
          </Form.Item>
          <Form.Item label="任务类型">
            <Select
              v-model:value="filterTaskType"
              :options="taskTypeFilterOptions"
              allow-clear
              placeholder="全部类型"
              style="width: 140px"
              @change="handleSearch"
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" @click="handleSearch">查询</Button>
              <Button @click="handleReset">重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id"
        @change="handleTableChange"
        :scroll="{ x: 1300 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_type'">
            <Tag>{{ taskTypeMap[record.task_type] || record.task_type }}</Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="taskStatusMap[record.status]?.color">
              {{ taskStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'success_rate'">
            <span :style="{ color: record.success_rate >= 95 ? '#52c41a' : record.success_rate >= 80 ? '#faad14' : '#ff4d4f' }">
              {{ record.success_rate != null ? `${record.success_rate}%` : '-' }}
            </span>
          </template>
          <template v-if="column.key === 'is_enabled'">
            <Switch :checked="record.is_enabled" size="small" @change="(v: boolean) => handleToggle(record.id, v)" />
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button v-access:code="'task:execute'" type="link" size="small" @click="handleExecute(record.id)">
                执行
              </Button>
              <Button type="link" size="small" @click="router.push(`/task/logs?task_id=${record.id}`)">
                日志
              </Button>
              <Button type="link" size="small" @click="router.push(`/task/monitor`)">
                监控
              </Button>
              <Popconfirm title="确认删除此任务？" @confirm="handleDelete(record.id)">
                <Button v-access:code="'task:delete'" type="link" size="small" danger>删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>
  </Page>
</template>
