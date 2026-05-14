<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Form, Input, Select, Space, Table, Tag, message, Modal, Popconfirm,
  Row, Col, DatePicker, Upload,
} from 'ant-design-vue';
import { getMeterList, createMeter, changeMeterStatus } from '#/api/modules/meter';
import { getProjectList, getMeterTypes, getWireTypes } from '#/api/modules/project';
import type { MeterListParams, MeterFormData } from '#/api/modules/meter';

const router = useRouter();
const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });
const expandedRowKeys = ref<number[]>([]);

const statusMap: Record<string, { color: string; text: string }> = {
  in_stock: { color: 'green', text: '在库' },
  testing: { color: 'blue', text: '挂表测试中' },
  test_complete: { color: 'cyan', text: '测试完成待拆' },
  borrowed: { color: 'orange', text: '借出' },
  repairing: { color: 'gold', text: '维修中' },
  scrapped: { color: 'red', text: '报废' },
};

const statusOptions = Object.entries(statusMap).map(([value, { text }]) => ({ value, label: text }));

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

const protocolOptions = [
  { value: 'DLMS', label: 'DLMS/COSEM' },
  { value: 'Modbus', label: 'Modbus' },
  { value: 'MQTT', label: 'MQTT' },
];

const columns = [
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
  ],
  testing: [
    { status: 'test_complete', label: '测试完成', confirm: '确认测试已完成？' },
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
  try {
    await createMeter(createForm.value);
    message.success('样机入库成功');
    showCreateModal.value = false;
    fetchData();
  } catch { message.error('入库失败'); }
}

async function handleChangeStatus(id: number, status: string) {
  try {
    await changeMeterStatus(id, { status, reason: `状态变更为${statusMap[status]?.text}` });
    message.success('状态变更成功');
    fetchData();
  } catch { message.error('状态变更失败'); }
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
          <Button type="primary" @click="showCreateModal = true">样机入库</Button>
          <Button @click="fetchData">刷新</Button>
        </Space>
      </template>

      <Table :columns="columns" :data-source="tableData" :loading="loading"
        :pagination="{ current: pagination.current, pageSize: pagination.pageSize, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id" @change="handleTableChange" :scroll="{ x: 1400 }" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'current_status'">
            <Tag :color="statusMap[record.current_status]?.color">
              {{ statusMap[record.current_status]?.text || record.current_status }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="goToDetail(record.id)">详情</Button>
              <template v-for="flow in (statusFlowMap[record.current_status] || [])" :key="flow.status">
                <Popconfirm :title="flow.confirm" @confirm="handleChangeStatus(record.id, flow.status)">
                  <Button type="link" size="small">{{ flow.label }}</Button>
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
  </Page>
</template>
