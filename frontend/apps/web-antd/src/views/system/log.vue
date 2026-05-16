<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import { Button, Card, DatePicker, Form, Select, Space, Table, Tag, message } from 'ant-design-vue';
import { getAuditLogs, exportAuditLogs } from '#/api/modules/system';
import { DEFAULT_PAGE_SIZE } from '#/constants';

const RangePicker = DatePicker.RangePicker;

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: DEFAULT_PAGE_SIZE });
const dateRange = ref<any>(null);
const searchForm = ref({
  operation_type: undefined as string | undefined,
  user_id: undefined as number | undefined,
  resource_type: undefined as string | undefined,
});

const opTypeMap: Record<string, { color: string; text: string }> = {
  CREATE: { color: 'green', text: '创建' },
  UPDATE: { color: 'blue', text: '修改' },
  DELETE: { color: 'red', text: '删除' },
  LOGIN: { color: 'cyan', text: '登录' },
};

const opTypeOptions = Object.entries(opTypeMap).map(([value, { label }]) => ({
  value,
  label: label || value,
}));

const resourceTypeOptions = [
  { value: 'meter', label: '设备' },
  { value: 'task', label: '任务' },
  { value: 'user', label: '用户' },
  { value: 'role', label: '角色' },
  { value: 'project', label: '项目' },
  { value: 'test', label: '测试' },
  { value: 'borrow', label: '借用' },
  { value: 'repair', label: '维修' },
];

const resourceTypeMap = Object.fromEntries(
  resourceTypeOptions.map(({ value, label }) => [value, label]),
);

const columns = [
  { title: '操作人', dataIndex: 'user_name', width: 100 },
  { title: '操作类型', dataIndex: 'operation_type', key: 'operation_type', width: 100 },
  { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 100 },
  { title: '资源ID', dataIndex: 'resource_id', width: 80 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 130 },
  { title: '时间', dataIndex: 'created_at', width: 180 },
  { title: '描述', dataIndex: 'description', ellipsis: true },
];

async function fetchData() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      ...searchForm.value,
    };
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.format?.('YYYY-MM-DD') || dateRange.value[0];
      params.end_date = dateRange.value[1]?.format?.('YYYY-MM-DD') || dateRange.value[1];
    }
    const res = await getAuditLogs(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } catch {
    message.error('获取操作日志失败');
  } finally { loading.value = false; }
}

function handleSearch() {
  pagination.value.current = 1;
  fetchData();
}

function handleReset() {
  searchForm.value = { operation_type: undefined, user_id: undefined, resource_type: undefined };
  dateRange.value = null;
  pagination.value.current = 1;
  fetchData();
}

async function handleExport() {
  try {
    const params: Record<string, any> = { ...searchForm.value };
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]?.format?.('YYYY-MM-DD') || dateRange.value[0];
      params.end_date = dateRange.value[1]?.format?.('YYYY-MM-DD') || dateRange.value[1];
    }

    const blob: Blob = await exportAuditLogs(params);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `操作日志_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败，请重试');
  }
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function formatJsonValues(values: any) {
  if (!values) return '-';
  try {
    return typeof values === 'string' ? JSON.stringify(JSON.parse(values), null, 2) : JSON.stringify(values, null, 2);
  } catch {
    return String(values);
  }
}

onMounted(() => { fetchData(); });
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline" :model="searchForm">
        <Form.Item label="操作类型">
          <Select v-model:value="searchForm.operation_type" allow-clear placeholder="全部" style="width: 120px"
            :options="opTypeOptions" />
        </Form.Item>
        <Form.Item label="资源类型">
          <Select v-model:value="searchForm.resource_type" allow-clear placeholder="全部" style="width: 120px"
            :options="resourceTypeOptions" />
        </Form.Item>
        <Form.Item label="日期范围">
          <RangePicker v-model:value="dateRange" style="width: 260px" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" @click="handleSearch">查询</Button>
            <Button @click="handleReset">重置</Button>
            <Button @click="handleExport">
              导出
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
    <Card :bordered="false" title="操作日志">
      <Table :columns="columns" :data-source="tableData" :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'operation_type'">
            <Tag :color="opTypeMap[record.operation_type]?.color">{{ opTypeMap[record.operation_type]?.text }}</Tag>
          </template>
          <template v-if="column.key === 'resource_type'">
            <Tag>{{ resourceTypeMap[record.resource_type] || record.resource_type }}</Tag>
          </template>
        </template>
        <template #expandedRowRender="{ record }">
          <div style="padding: 8px 0">
            <div v-if="record.old_values" style="margin-bottom: 8px">
              <strong>变更前:</strong>
              <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; margin-top: 4px; font-size: 12px; max-height: 200px; overflow: auto">{{ formatJsonValues(record.old_values) }}</pre>
            </div>
            <div v-if="record.new_values">
              <strong>变更后:</strong>
              <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; margin-top: 4px; font-size: 12px; max-height: 200px; overflow: auto">{{ formatJsonValues(record.new_values) }}</pre>
            </div>
            <div v-if="!record.old_values && !record.new_values" style="color: #999">无详细变更数据</div>
          </div>
        </template>
      </Table>
    </Card>
  </Page>
</template>
