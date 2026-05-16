<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Button, Card, Form, Input, Select, Space, Switch, Table, Tag, Popconfirm, message } from 'ant-design-vue';
import { getTaskList, executeTask, toggleTask, deleteTask } from '#/api/modules/task';
import { TASK_STATUS_MAP, TASK_TYPE_MAP, TASK_CATEGORY_MAP, DEFAULT_PAGE_SIZE, THEME_COLORS } from '#/constants';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: DEFAULT_PAGE_SIZE });

// Search and filter state
const searchKeyword = ref('');
const filterStatus = ref<string | undefined>(undefined);
const filterTaskType = ref<string | undefined>(undefined);
const filterTaskCategory = ref<string | undefined>(undefined);

const taskStatusMap = Object.fromEntries(
  Object.entries(TASK_STATUS_MAP).map(([key, val]) => [key, { color: val.color, text: val.label }]),
);
const taskTypeMap = TASK_TYPE_MAP;
const taskCategoryMap = Object.fromEntries(
  Object.entries(TASK_CATEGORY_MAP).map(([key, val]) => [key, { color: val.color, text: val.label }]),
);

const statusFilterOptions = Object.entries(TASK_STATUS_MAP).map(([value, { label }]) => ({ value, label }));

const taskTypeFilterOptions = Object.entries(TASK_TYPE_MAP).map(([value, label]) => ({ value, label }));

const taskCategoryFilterOptions = Object.entries(TASK_CATEGORY_MAP).map(([value, { label }]) => ({ value, label }));

const columns = [
  { title: '任务名称', dataIndex: 'task_name', width: 200, ellipsis: true },
  { title: '任务分类', dataIndex: 'task_category', key: 'task_category', width: 110 },
  { title: '调度类型', dataIndex: 'task_type', key: 'task_type', width: 110 },
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
    if (filterTaskCategory.value) params.task_category = filterTaskCategory.value;
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
  filterTaskCategory.value = undefined;
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
    <Card :bordered="false" title="任务列表">
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
          <Form.Item label="任务分类">
            <Select
              v-model:value="filterTaskCategory"
              :options="taskCategoryFilterOptions"
              allow-clear
              placeholder="全部分类"
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
        :scroll="{ x: 1400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_category'">
            <Tag :color="taskCategoryMap[record.task_category]?.color || 'default'">
              {{ taskCategoryMap[record.task_category]?.text || record.task_category || '-' }}
            </Tag>
          </template>
          <template v-if="column.key === 'task_type'">
            <Tag>{{ taskTypeMap[record.task_type] || record.task_type }}</Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="taskStatusMap[record.status]?.color">
              {{ taskStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'success_rate'">
            <span :style="{ color: record.success_rate >= 95 ? THEME_COLORS.SUCCESS : record.success_rate >= 80 ? THEME_COLORS.WARNING : THEME_COLORS.ERROR }">
              {{ record.success_rate != null ? `${record.success_rate}%` : '-' }}
            </span>
          </template>
          <template v-if="column.key === 'is_enabled'">
            <Switch :checked="record.is_enabled" size="small" @change="(v: any) => handleToggle(record.id, !!v)" />
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
