<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, Card, Form, Input, Modal, Select, Space, Table, Tag, Popconfirm, message } from 'ant-design-vue';
import { getUserList, createUser, updateUser, deleteUser, resetUserPassword, getRoleList } from '#/api/modules/system';
import type { UserFormData } from '#/api/modules/system';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

const showModal = ref(false);
const modalTitle = ref('新增用户');
const editingId = ref<number | null>(null);
const roles = ref<any[]>([]);

const formState = ref<UserFormData>({
  username: '', name: '', email: '', phone: '', role_ids: [], password: '',
});

const columns = [
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '姓名', dataIndex: 'name', width: 100 },
  { title: '邮箱', dataIndex: 'email', width: 200 },
  { title: '手机号', dataIndex: 'phone', width: 130 },
  { title: '角色', dataIndex: 'roles', key: 'roles', width: 200 },
  { title: '创建时间', dataIndex: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' },
];

async function fetchData() {
  loading.value = true;
  try { const res = await getUserList({ page: pagination.value.current, page_size: pagination.value.pageSize }); tableData.value = res.items || []; total.value = res.total || 0; }
  finally { loading.value = false; }
}

async function fetchRoles() {
  try { const res = await getRoleList(); roles.value = res.items || res || []; } catch { /* ignore */ }
}

function openCreate() {
  editingId.value = null;
  modalTitle.value = '新增用户';
  formState.value = { username: '', name: '', email: '', phone: '', role_ids: [], password: '' };
  showModal.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  modalTitle.value = '编辑用户';
  formState.value = { username: record.username, name: record.name, email: record.email, phone: record.phone, role_ids: record.role_ids || [], password: '' };
  showModal.value = true;
}

async function handleSubmit() {
  try {
    if (editingId.value) {
      await updateUser(editingId.value, formState.value);
      message.success('更新成功');
    } else {
      await createUser(formState.value);
      message.success('创建成功');
    }
    showModal.value = false;
    fetchData();
  } catch { message.error('操作失败'); }
}

async function handleDelete(id: number) {
  try { await deleteUser(id); message.success('已删除'); fetchData(); } catch { message.error('删除失败'); }
}

async function handleResetPwd(id: number) {
  try { await resetUserPassword(id, '123456'); message.success('密码已重置为 123456'); } catch { message.error('重置失败'); }
}

function handleTableChange(pag: any) { pagination.value.current = pag.current; pagination.value.pageSize = pag.pageSize; fetchData(); }

onMounted(() => { fetchData(); fetchRoles(); });
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="用户管理">
      <template #extra>
        <Space>
          <Button type="primary" v-access:code="'system:user:create'" @click="openCreate">新增用户</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>
      <Table :columns="columns" :data-source="tableData" :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true }"
        row-key="id" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'roles'">
            <Tag v-for="role in (record.roles || [])" :key="role" color="blue">{{ role }}</Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">编辑</Button>
              <Popconfirm title="重置密码为 123456？" @confirm="handleResetPwd(record.id)">
                <Button type="link" size="small">重置密码</Button>
              </Popconfirm>
              <Popconfirm title="确认删除？" @confirm="handleDelete(record.id)">
                <Button type="link" size="small" danger>删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal v-model:open="showModal" :title="modalTitle" @ok="handleSubmit" width="500px">
      <Form :model="formState" layout="vertical" style="margin-top: 16px">
        <Form.Item label="用户名" required><Input v-model:value="formState.username" :disabled="!!editingId" /></Form.Item>
        <Form.Item label="姓名" required><Input v-model:value="formState.name" /></Form.Item>
        <Form.Item label="邮箱" required><Input v-model:value="formState.email" /></Form.Item>
        <Form.Item label="手机号"><Input v-model:value="formState.phone" /></Form.Item>
        <Form.Item label="密码" v-if="!editingId" required><Input.Password v-model:value="formState.password" /></Form.Item>
        <Form.Item label="角色">
          <Select v-model:value="formState.role_ids" mode="multiple" :options="roles.map((r: any) => ({ value: r.id, label: r.name }))" placeholder="选择角色" />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
