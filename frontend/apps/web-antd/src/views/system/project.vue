<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
  Modal,
  Popconfirm,
  Select,
  SelectOption,
  Space,
  Table,
  Tag,
  message,
} from 'ant-design-vue';
import {
  getProjectList,
  createProject,
  updateProject,
  deleteProject,
} from '#/api/modules/project';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Modal state
const showModal = ref(false);
const modalTitle = ref('新增项目');
const editingId = ref<number | null>(null);
const submitting = ref(false);

const formState = ref({
  name: '',
  description: '',
  test_leader_name: '',
  dev_leader_name: '',
  status: 'active',
});

const statusOptions = [
  { label: '进行中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '已归档', value: 'archived' },
];

const statusColorMap: Record<string, string> = {
  active: 'green',
  completed: 'blue',
  archived: 'default',
};

function formatStatus(status: string) {
  const map: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    archived: '已归档',
  };
  return map[status] || status;
}

const columns: any[] = [
  { title: '项目名称', dataIndex: 'name', width: 160 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '测试负责人', dataIndex: 'test_leader', width: 120 },
  { title: '开发负责人', dataIndex: 'dev_leader', width: 120 },
  { title: '设备数量', dataIndex: 'meter_count', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getProjectList({ page: pagination.value.current });
    tableData.value = res.items || res || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  modalTitle.value = '新增项目';
  formState.value = {
    name: '',
    description: '',
    test_leader_name: '',
    dev_leader_name: '',
    status: 'active',
  };
  showModal.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  modalTitle.value = '编辑项目';
  formState.value = {
    name: record.name || '',
    description: record.description || '',
    test_leader_name: record.test_leader || record.test_leader_name || '',
    dev_leader_name: record.dev_leader || record.dev_leader_name || '',
    status: record.status || 'active',
  };
  showModal.value = true;
}

async function handleSubmit() {
  if (!formState.value.name) {
    message.warning('请填写项目名称');
    return;
  }
  submitting.value = true;
  try {
    const payload: any = { ...formState.value };
    if (editingId.value) {
      await updateProject(editingId.value, payload);
      message.success('更新成功');
    } else {
      await createProject(payload);
      message.success('创建成功');
    }
    showModal.value = false;
    fetchData();
  } catch {
    message.error('操作失败');
  } finally {
    submitting.value = false;
  }
}

async function handleDelete(id: number) {
  try {
    await deleteProject(id);
    message.success('已删除');
    fetchData();
  } catch {
    message.error('删除失败');
  }
}

function goToMeterList(projectId: number) {
  router.push({ path: '/meter/list', query: { project_id: String(projectId) } });
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
    <Card :bordered="false" title="项目管理">
      <template #extra>
        <Space>
          <Button type="primary" @click="openCreate">新增项目</Button>
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
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="statusColorMap[record.status] || 'default'">
              {{ formatStatus(record.status) }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">
                编辑
              </Button>
              <Button type="link" size="small" @click="goToMeterList(record.id)">
                查看设备
              </Button>
              <Popconfirm
                title="确认删除该项目？删除后不可恢复"
                @confirm="handleDelete(record.id)"
              >
                <Button type="link" size="small" danger>删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="showModal"
      :title="modalTitle"
      :confirm-loading="submitting"
      @ok="handleSubmit"
      width="560px"
    >
      <Form :model="formState" layout="vertical" style="margin-top: 16px">
        <FormItem label="项目名称" required>
          <Input
            v-model:value="formState.name"
            placeholder="输入项目名称"
          />
        </FormItem>
        <FormItem label="描述">
          <Input.TextArea
            v-model:value="formState.description"
            :rows="3"
            placeholder="输入项目描述"
          />
        </FormItem>
        <FormItem label="测试负责人">
          <Input
            v-model:value="formState.test_leader_name"
            placeholder="输入测试负责人姓名"
          />
        </FormItem>
        <FormItem label="开发负责人">
          <Input
            v-model:value="formState.dev_leader_name"
            placeholder="输入开发负责人姓名"
          />
        </FormItem>
        <FormItem label="状态">
          <Select v-model:value="formState.status">
            <SelectOption
              v-for="opt in statusOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
