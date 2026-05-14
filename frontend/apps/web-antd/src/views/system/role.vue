<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, Card, Form, Input, Modal, Space, Table, Tag, Tree, Popconfirm, message } from 'ant-design-vue';
import { getRoleList, createRole, updateRole, deleteRole, getPermissionTree } from '#/api/modules/system';
import type { RoleFormData } from '#/api/modules/system';

const loading = ref(false);
const tableData = ref<any[]>([]);
const showModal = ref(false);
const modalTitle = ref('新增角色');
const editingId = ref<number | null>(null);
const permissionTree = ref<any[]>([]);

const formState = ref<RoleFormData>({ name: '', code: '', description: '', permission_ids: [] });

// Default permissions tree for UI display
const defaultPermissions = [
  { id: 1, name: '设备管理', children: [
    { id: 11, name: '查看设备' }, { id: 12, name: '新增设备' }, { id: 13, name: '编辑设备' }, { id: 14, name: '删除设备' },
  ]},
  { id: 2, name: '采集任务', children: [
    { id: 21, name: '查看任务' }, { id: 22, name: '创建任务' }, { id: 23, name: '执行任务' }, { id: 24, name: '删除任务' },
  ]},
  { id: 3, name: '数据分析', children: [
    { id: 31, name: '查看分析' }, { id: 32, name: '导出报告' },
  ]},
  { id: 4, name: '测试管理', children: [
    { id: 41, name: '查看测试' }, { id: 42, name: '创建报告' }, { id: 43, name: '管理缺陷' },
  ]},
  { id: 5, name: '系统管理', children: [
    { id: 51, name: '用户管理' }, { id: 52, name: '角色管理' }, { id: 53, name: '查看日志' },
  ]},
];

const columns = [
  { title: '角色名称', dataIndex: 'name', width: 150 },
  { title: '角色编码', dataIndex: 'code', width: 200 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
  { title: '用户数', dataIndex: 'user_count', width: 80 },
  { title: '操作', key: 'action', width: 180 },
];

async function fetchData() {
  loading.value = true;
  try { const res = await getRoleList(); tableData.value = res.items || res || []; } finally { loading.value = false; }
}

async function fetchPermissions() {
  try { permissionTree.value = await getPermissionTree(); } catch { permissionTree.value = defaultPermissions; }
}

function openCreate() {
  editingId.value = null;
  modalTitle.value = '新增角色';
  formState.value = { name: '', code: '', description: '', permission_ids: [] };
  showModal.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  modalTitle.value = '编辑角色';
  formState.value = { name: record.name, code: record.code, description: record.description || '', permission_ids: record.permission_ids || [] };
  showModal.value = true;
}

async function handleSubmit() {
  try {
    if (editingId.value) { await updateRole(editingId.value, formState.value); message.success('更新成功'); }
    else { await createRole(formState.value); message.success('创建成功'); }
    showModal.value = false; fetchData();
  } catch { message.error('操作失败'); }
}

async function handleDelete(id: number) {
  try { await deleteRole(id); message.success('已删除'); fetchData(); } catch { message.error('删除失败'); }
}

onMounted(() => { fetchData(); fetchPermissions(); });
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="角色管理">
      <template #extra>
        <Space>
          <Button type="primary" v-access:code="'system:role:create'" @click="openCreate">新增角色</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>
      <Table :columns="columns" :data-source="tableData" :loading="loading" row-key="id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">编辑</Button>
              <Button type="link" size="small">分配权限</Button>
              <Popconfirm title="确认删除？删除后不可恢复" @confirm="handleDelete(record.id)">
                <Button type="link" size="small" danger>删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal v-model:open="showModal" :title="modalTitle" @ok="handleSubmit" width="600px">
      <Form :model="formState" layout="vertical" style="margin-top: 16px">
        <Form.Item label="角色名称" required><Input v-model:value="formState.name" /></Form.Item>
        <Form.Item label="角色编码" required><Input v-model:value="formState.code" placeholder="如: lab_admin, test_leader" /></Form.Item>
        <Form.Item label="描述"><Input.TextArea v-model:value="formState.description" :rows="2" /></Form.Item>
        <Form.Item label="权限配置">
          <Tree v-model:checkedKeys="formState.permission_ids" :tree-data="permissionTree" checkable
            :field-names="{ title: 'name', key: 'id', children: 'children' }"
            default-expand-all />
        </Form.Item>
      </Form>
    </Modal>
  </Page>
</template>
