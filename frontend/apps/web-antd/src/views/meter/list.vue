<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Form, Input, Select, Space, Table, Tag, message, Modal, Popconfirm,
  Row, Col, Upload,
} from 'ant-design-vue';
import { getMeterList, createMeter, changeMeterStatus, importMeters, exportMeters } from '#/api/modules/meter';
import { getProjectList, getMeterTypes, getWireTypes } from '#/api/modules/project';
import type { MeterListParams, MeterFormData } from '#/api/modules/meter';
import { METER_STATUS_MAP, PROTOCOL_OPTIONS, DEFAULT_PAGE_SIZE } from '#/constants';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: DEFAULT_PAGE_SIZE });

const statusMap = METER_STATUS_MAP;

const statusOptions = Object.entries(statusMap).map(([value, { label }]) => ({ value, label }));

const searchForm = ref<MeterListParams>({ keyword: '', status: undefined, project_id: undefined });

const showCreateModal = ref(false);
const createForm = ref<MeterFormData>({
  serial_number: '', meter_name: '', meter_type_id: undefined as any,
  project_id: undefined as any, protocol: 'DLMS', line_type: '3P4W',
  manufacturer: '', model: '', firmware_version: '', hardware_version: '',
  frame_number: '', location: '', factory_date: '', purchase_date: '',
  warranty_date: '', notes: '',
});

// Metadata for dropdowns
const projects = ref<any[]>([]);
const meterTypes = ref<any[]>([]);
const wireTypes = ref<any[]>([]);

const protocolOptions = PROTOCOL_OPTIONS;

const columns: any[] = [
  { title: '出厂编号', dataIndex: 'serial_number', key: 'serial_number', width: 140 },
  { title: '表计名称', dataIndex: 'meter_name', key: 'meter_name', width: 150 },
  { title: '项目', dataIndex: 'project_name', key: 'project_name', width: 120 },
  { title: '表型', dataIndex: 'meter_type', key: 'meter_type', width: 80 },
  { title: '协议', dataIndex: 'protocol', key: 'protocol', width: 90 },
  { title: '线制', dataIndex: 'line_type', key: 'line_type', width: 80 },
  { title: '状态', dataIndex: 'current_status', key: 'current_status', width: 120 },
  { title: '位置', dataIndex: 'location', key: 'location', width: 110 },
  { title: '入库时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
];

const statusFlowMap: Record<string, Array<{ status: string; label: string; confirm: string }>> = {
  in_stock: [
    { status: 'testing', label: '开始测试', confirm: '确认开始挂表测试？' },
    { status: 'borrowed', label: '借出', confirm: '确认借出？需走审批流程' },
    { status: 'repairing', label: '送修', confirm: '确认送修？' },
    { status: 'scrapped', label: '报废', confirm: '确认报废？报废后不可恢复' },
  ],
  testing: [
    { status: 'test_complete', label: '测试完成', confirm: '确认测试已完成？' },
    { status: 'repairing', label: '送修', confirm: '确认送修？' },
  ],
  test_complete: [
    { status: 'in_stock', label: '拆表归库', confirm: '确认拆表归库？' },
  ],
  borrowed: [
    { status: 'in_stock', label: '归还', confirm: '确认归还？' },
  ],
};

async function fetchData() {
  loading.value = true;
  try {
    const res = await getMeterList({
      page: pagination.value.current, page_size: pagination.value.pageSize,
      ...searchForm.value,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } catch {
    message.error('获取设备列表失败');
  } finally { loading.value = false; }
}

async function fetchMetadata() {
  try {
    const [projRes, typeRes, wireRes] = await Promise.all([
      getProjectList(), getMeterTypes(), getWireTypes(),
    ]);
    projects.value = projRes.items || projRes || [];
    meterTypes.value = typeRes.items || typeRes || [];
    wireTypes.value = wireRes.items || wireRes || [];
  } catch { /* use defaults */ }
}

function handleSearch() { pagination.value.current = 1; fetchData(); }
function handleReset() { searchForm.value = { keyword: '', status: undefined, project_id: undefined }; handleSearch(); }
function handleTableChange(pag: any) { pagination.value.current = pag.current; pagination.value.pageSize = pag.pageSize; fetchData(); }
function goToDetail(id: number) { router.push(`/meter/detail/${id}`); }

async function handleCreate() {
  if (!createForm.value.serial_number || !createForm.value.meter_name) {
    message.warning('请填写出厂编号和表计名称');
    return;
  }
  try {
    await createMeter(createForm.value);
    message.success('样机入库成功');
    showCreateModal.value = false;
    fetchData();
  } catch { message.error('入库失败'); }
}

async function handleChangeStatus(id: number, status: string) {
  try {
    await changeMeterStatus(id, { status, reason: `状态变更为${statusMap[status]?.label}` });
    message.success('状态变更成功');
    fetchData();
  } catch { message.error('状态变更失败'); }
}

// --- Batch import ---
const showImportModal = ref(false);
const importFileList = ref<any[]>([]);
const importPreviewData = ref<any[]>([]);
const importLoading = ref(false);

const importColumns = [
  { title: '出厂编号', dataIndex: 'serial_number', width: 140 },
  { title: '表计名称', dataIndex: 'meter_name', width: 130 },
  { title: '厂商', dataIndex: 'manufacturer', width: 100 },
  { title: '型号', dataIndex: 'model', width: 100 },
  { title: '协议', dataIndex: 'protocol', width: 80 },
];

function handleImportUpload(info: any) {
  importFileList.value = info.fileList.slice(-1);
  // Preview will be populated after server response
  if (info.file.status === 'done' && info.file.response) {
    importPreviewData.value = info.file.response?.items || [];
  } else if (info.file.status === 'error') {
    message.error('文件解析失败，请检查文件格式');
  }
}

function handleBeforeUpload(file: File) {
  const validExts = ['.xlsx', '.xls', '.csv'];
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  if (!validExts.includes(ext)) {
    message.error('仅支持 .xlsx、.xls、.csv 文件');
    return Upload.LIST_IGNORE;
  }
  return true;
}

async function handleImportConfirm() {
  if (!importFileList.value.length) {
    message.warning('请先上传文件');
    return;
  }
  const file = importFileList.value[0]?.originFileObj || importFileList.value[0];
  if (!file) {
    message.warning('请先上传文件');
    return;
  }
  importLoading.value = true;
  try {
    await importMeters(file);
    message.success('批量导入成功');
    showImportModal.value = false;
    importFileList.value = [];
    importPreviewData.value = [];
    fetchData();
  } catch {
    message.error('批量导入失败');
  } finally {
    importLoading.value = false;
  }
}

function handleDownloadTemplate() {
  message.info('模板下载功能开发中，请联系管理员获取导入模板');
}

async function handleExportMeters() {
  try {
    const blob = await exportMeters({
      ...searchForm.value,
    });
    const url = window.URL.createObjectURL(blob as any);
    const a = document.createElement('a');
    a.href = url;
    a.download = `样机列表_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败');
  }
}

onMounted(() => { fetchData(); fetchMetadata(); });
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Form layout="inline" :model="searchForm">
        <Form.Item label="关键词">
          <Input v-model:value="searchForm.keyword" placeholder="编号/名称/厂商" allow-clear style="width: 180px" />
        </Form.Item>
        <Form.Item label="状态">
          <Select v-model:value="searchForm.status" :options="statusOptions" placeholder="全部" allow-clear style="width: 140px" />
        </Form.Item>
        <Form.Item label="项目">
          <Select v-model:value="searchForm.project_id" placeholder="全部项目" allow-clear style="width: 160px"
            :options="projects.map((p: any) => ({ value: p.id, label: p.name }))" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" @click="handleSearch">查询</Button>
            <Button @click="handleReset">重置</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    <Card :bordered="false">
      <template #title>
        <Space><span>样机列表</span><Tag color="blue">{{ total }} 台</Tag></Space>
      </template>
      <template #extra>
        <Space>
          <Button type="primary" v-access:code="'meter:create'" @click="showCreateModal = true">样机入库</Button>
          <Button v-access:code="'meter:create'" @click="showImportModal = true">批量导入</Button>
          <Button @click="handleExportMeters">导出</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>

      <Table :columns="columns" :data-source="tableData" :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id" @change="handleTableChange" :scroll="{ x: 1400 }" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'current_status'">
            <Tag :color="statusMap[record.current_status]?.color">
              {{ statusMap[record.current_status]?.label || record.current_status }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record.id)">详情</Button>
              <template v-for="flow in (statusFlowMap[record.current_status] || [])" :key="flow.status">
                <Popconfirm :title="flow.confirm" @confirm="handleChangeStatus(record.id, flow.status)">
                  <Button v-access:code="'meter:update'" type="link" size="small">{{ flow.label }}</Button>
                </Popconfirm>
              </template>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- 样机入库登记 Modal - PRD US-001 -->
    <Modal v-model:open="showCreateModal" title="样机入库登记" @ok="handleCreate" width="720px" :maskClosable="false">
      <Form :model="createForm" layout="vertical" style="margin-top: 16px">
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="出厂编号" required><Input v-model:value="createForm.serial_number" placeholder="唯一标识" /></Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="表计名称" required><Input v-model:value="createForm.meter_name" placeholder="如: Coral测试表01" /></Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="表计类型" required>
              <Select v-model:value="createForm.meter_type_id" placeholder="选择表型"
                :options="meterTypes.map((t: any) => ({ value: t.id, label: `${t.name} (${t.code})` }))" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="所属项目" required>
              <Select v-model:value="createForm.project_id" placeholder="选择项目"
                :options="projects.map((p: any) => ({ value: p.id, label: p.name }))" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="通信协议" required>
              <Select v-model:value="createForm.protocol" :options="protocolOptions" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="线制类型">
              <Select v-model:value="createForm.line_type"
                :options="wireTypes.map((w: any) => ({ value: w.code, label: w.name }))" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="厂商"><Input v-model:value="createForm.manufacturer" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="型号"><Input v-model:value="createForm.model" placeholder="如: DCSP, DCPP" /></Form.Item></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="软件版本"><Input v-model:value="createForm.firmware_version" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="硬件版本"><Input v-model:value="createForm.hardware_version" /></Form.Item></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="框编号"><Input v-model:value="createForm.frame_number" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="放置位置"><Input v-model:value="createForm.location" /></Form.Item></Col>
        </Row>
        <Form.Item label="备注"><Input.TextArea v-model:value="createForm.notes" :rows="2" /></Form.Item>
      </Form>
    </Modal>

    <!-- 批量导入 Modal - PRD US-001 -->
    <Modal v-model:open="showImportModal" title="批量导入样机" width="720px" :maskClosable="false"
      :footer="null">
      <div style="margin-top: 16px">
        <Upload
          :file-list="importFileList"
          :before-upload="handleBeforeUpload"
          :custom-request="(options: any) => { options.onSuccess({}, options.file); }"
          @change="handleImportUpload"
          accept=".xlsx,.xls,.csv"
          :max-count="1"
        >
          <Button type="primary">选择文件</Button>
        </Upload>
        <div style="margin: 8px 0; color: #999; font-size: 12px">
          支持 .xlsx、.xls、.csv 格式
          <Button type="link" size="small" @click="handleDownloadTemplate" style="padding: 0; margin-left: 8px">下载导入模板</Button>
        </div>

        <div v-if="importPreviewData.length > 0" style="margin-top: 16px">
          <div style="margin-bottom: 8px; font-weight: 500">预览数据 ({{ importPreviewData.length }} 条)</div>
          <Table :columns="importColumns" :data-source="importPreviewData" size="small"
            :pagination="{ pageSize: 5 }" row-key="serial_number" />
        </div>

        <div style="margin-top: 16px; text-align: right">
          <Space>
            <Button @click="showImportModal = false">取消</Button>
            <Button type="primary" :loading="importLoading" @click="handleImportConfirm">确认导入</Button>
          </Space>
        </div>
      </div>
    </Modal>
  </Page>
</template>
