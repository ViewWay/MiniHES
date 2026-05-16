<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Descriptions, DescriptionsItem, Tag, Tabs, TabPane, Timeline, TimelineItem,
  Table, Space, Modal, Form, Input, Upload, message, Popconfirm, Row, Col, Select, InputNumber, Switch,
} from 'ant-design-vue';
import { getMeterDetail, updateMeter, changeMeterStatus, getMeterStatusHistory, getMeterAttachments, uploadMeterAttachment, updateMeterComm } from '#/api/modules/meter';
import type { UploadProps } from 'ant-design-vue';
import StatusBadge from '#/components/meter/StatusBadge.vue';
import BorrowDialog from '#/components/meter/BorrowDialog.vue';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const meterDetail = ref<any>(null);
const activeTab = ref('info');

const showBorrowDialog = ref(false);
const showStatusDialog = ref(false);
const statusForm = ref({ status: '', reason: '' });

const statusFlowOptions: Record<string, Array<{ value: string; label: string }>> = {
  in_stock: [{ value: 'testing', label: '开始挂表测试' }, { value: 'borrowed', label: '借出' }, { value: 'repairing', label: '送修' }, { value: 'scrapped', label: '报废' }],
  testing: [{ value: 'test_complete', label: '测试完成' }, { value: 'repairing', label: '送修' }],
  test_complete: [{ value: 'in_stock', label: '拆表归库' }, { value: 'repairing', label: '送修' }],
  borrowed: [{ value: 'in_stock', label: '归还' }, { value: 'repairing', label: '送修' }],
  repairing: [{ value: 'in_stock', label: '修好归库' }, { value: 'scrapped', label: '报废' }],
};

// Status history (loaded from API)
const statusHistory = ref<any[]>([]);

// Attachments (loaded from API)
const attachments = ref<any[]>([]);

const attachColumns = [
  { title: '文件名', dataIndex: 'name' },
  { title: '大小', dataIndex: 'size', width: 80 },
  { title: '上传人', dataIndex: 'uploaded_by', width: 80 },
  { title: '上传时间', dataIndex: 'uploaded_at', width: 120 },
  { title: '操作', key: 'action', width: 80 },
];

async function fetchDetail() {
  const id = route.params.id;
  if (!id) return;
  loading.value = true;
  try {
    meterDetail.value = await getMeterDetail(Number(id));
    // Fetch status history
    try {
      const historyRes = await getMeterStatusHistory(Number(id));
      statusHistory.value = historyRes.items || historyRes || [];
    } catch { /* use empty */ }
    // Fetch attachments
    try {
      const attachRes = await getMeterAttachments(Number(id));
      attachments.value = attachRes.items || attachRes || [];
    } catch { /* use empty */ }
  } finally { loading.value = false; }
}

async function handleStatusChange() {
  if (!meterDetail.value || !statusForm.value.status) return;
  try {
    await changeMeterStatus(meterDetail.value.id, statusForm.value);
    message.success('状态变更成功');
    showStatusDialog.value = false;
    fetchDetail();
  } catch { message.error('状态变更失败'); }
}

function goBack() { router.push('/meter/list'); }

const uploading = ref(false);

const handleUpload: UploadProps['customRequest'] = async (options) => {
  const { file, onSuccess, onError } = options;
  const meterId = Number(route.params.id);
  try {
    uploading.value = true;
    await uploadMeterAttachment(meterId, file as File);
    onSuccess?.(null);
    message.success('上传成功');
    // Refresh attachments
    try {
      const res = await getMeterAttachments(meterId);
      attachments.value = res.items || res || [];
    } catch { /* ignore */ }
  } catch (err) {
    onError?.(err as Error);
    message.error('上传失败');
  } finally {
    uploading.value = false;
  }
};

onMounted(() => { fetchDetail(); });

// --- Meter edit modal (PRD §3.1.4) ---
const showEditModal = ref(false);
const editForm = ref<Record<string, any>>({});
const editLoading = ref(false);
const projects = ref<any[]>([]);
const meterTypes = ref<any[]>([]);
const wireTypes = ref<any[]>([]);

const protocolOptions = [
  { value: 'DLMS', label: 'DLMS/COSEM' },
  { value: 'Modbus', label: 'Modbus' },
  { value: 'MQTT', label: 'MQTT' },
];

async function fetchMetadata() {
  try {
    const { getProjectList, getMeterTypes, getWireTypes } = await import('#/api/modules/project');
    const [projRes, typeRes, wireRes] = await Promise.all([
      getProjectList(), getMeterTypes(), getWireTypes(),
    ]);
    projects.value = projRes.items || projRes || [];
    meterTypes.value = typeRes.items || typeRes || [];
    wireTypes.value = wireRes.items || wireRes || [];
  } catch { /* use defaults */ }
}

function openEditModal() {
  if (!meterDetail.value) return;
  editForm.value = {
    serial_number: meterDetail.value.serial_number || '',
    meter_name: meterDetail.value.meter_name || '',
    meter_type_id: meterDetail.value.meter_type_id,
    project_id: meterDetail.value.project_id,
    protocol: meterDetail.value.protocol || 'DLMS',
    line_type: meterDetail.value.line_type || '',
    manufacturer: meterDetail.value.manufacturer || '',
    model: meterDetail.value.model || '',
    firmware_version: meterDetail.value.firmware_version || '',
    hardware_version: meterDetail.value.hardware_version || '',
    frame_number: meterDetail.value.frame_number || '',
    location: meterDetail.value.location || '',
    factory_date: meterDetail.value.factory_date || '',
    purchase_date: meterDetail.value.purchase_date || '',
    warranty_date: meterDetail.value.warranty_date || '',
    notes: meterDetail.value.notes || '',
  };
  showEditModal.value = true;
}

async function handleEditSubmit() {
  if (!meterDetail.value) return;
  editLoading.value = true;
  try {
    await updateMeter(meterDetail.value.id, editForm.value);
    message.success('信息更新成功');
    showEditModal.value = false;
    fetchDetail();
  } catch {
    message.error('信息更新失败');
  } finally {
    editLoading.value = false;
  }
}

// --- Communication config edit modal (PRD §5.2.3) ---
const showCommEditModal = ref(false);
const commForm = ref<Record<string, any>>({});
const commLoading = ref(false);

const connectionTypeOptions = [
  { value: 'tcp', label: 'TCP' },
  { value: 'serial', label: '串口' },
  { value: 'udp', label: 'UDP' },
];

function openCommEditModal() {
  if (!meterDetail.value?.communication) return;
  const comm = meterDetail.value.communication;
  commForm.value = {
    connection_type: comm.connection_type || 'tcp',
    host: comm.host || '',
    port: comm.port ?? 0,
    device_address: comm.device_address || '',
    baud_rate: comm.baud_rate ?? 9600,
    timeout: comm.timeout ?? 30,
    is_enabled: !!comm.is_enabled,
  };
  showCommEditModal.value = true;
}

async function handleCommEditSubmit() {
  if (!meterDetail.value) return;
  commLoading.value = true;
  try {
    await updateMeterComm(meterDetail.value.id, commForm.value);
    message.success('通信配置更新成功');
    showCommEditModal.value = false;
    fetchDetail();
  } catch {
    message.error('通信配置更新失败');
  } finally {
    commLoading.value = false;
  }
}

fetchMetadata();
</script>

<template>
  <Page auto-content-height>
    <div style="margin-bottom: 16px">
      <Button type="text" @click="goBack">← 返回列表</Button>
    </div>

    <template v-if="meterDetail">
      <Card :bordered="false" style="margin-bottom: 16px">
        <template #title>
          <Space>
            <span style="font-size: 18px; font-weight: 600">{{ meterDetail.meter_name }}</span>
            <Tag>{{ meterDetail.serial_number }}</Tag>
            <StatusBadge :status="meterDetail.current_status" />
          </Space>
        </template>
        <template #extra>
          <Space>
            <Button @click="openEditModal">编辑</Button>
            <template v-for="opt in (statusFlowOptions[meterDetail.current_status] || [])" :key="opt.value">
              <Button v-if="opt.value === 'borrowed'" type="primary" @click="showBorrowDialog = true">{{ opt.label }}</Button>
              <Popconfirm v-else :title="`确认${opt.label}？`" @confirm=";(statusForm.status = opt.value), (statusForm.reason = opt.label), handleStatusChange()">
                <Button>{{ opt.label }}</Button>
              </Popconfirm>
            </template>
          </Space>
        </template>
      </Card>

      <Card :bordered="false">
        <Tabs v-model:activeKey="activeTab">
          <TabPane key="info" tab="基本信息">
            <Descriptions :column="3" bordered size="middle">
              <DescriptionsItem label="出厂编号">{{ meterDetail.serial_number }}</DescriptionsItem>
              <DescriptionsItem label="表计名称">{{ meterDetail.meter_name }}</DescriptionsItem>
              <DescriptionsItem label="表计类型">{{ meterDetail.meter_type }}</DescriptionsItem>
              <DescriptionsItem label="所属项目">{{ meterDetail.project_name }}</DescriptionsItem>
              <DescriptionsItem label="通信协议">{{ meterDetail.protocol }}</DescriptionsItem>
              <DescriptionsItem label="线制类型">{{ meterDetail.line_type }}</DescriptionsItem>
              <DescriptionsItem label="厂商">{{ meterDetail.manufacturer }}</DescriptionsItem>
              <DescriptionsItem label="型号">{{ meterDetail.model }}</DescriptionsItem>
              <DescriptionsItem label="软件版本">{{ meterDetail.firmware_version }}</DescriptionsItem>
              <DescriptionsItem label="硬件版本">{{ meterDetail.hardware_version }}</DescriptionsItem>
              <DescriptionsItem label="框编号">{{ meterDetail.frame_number }}</DescriptionsItem>
              <DescriptionsItem label="放置位置">{{ meterDetail.location }}</DescriptionsItem>
              <DescriptionsItem label="出厂日期">{{ meterDetail.factory_date }}</DescriptionsItem>
              <DescriptionsItem label="购买日期">{{ meterDetail.purchase_date }}</DescriptionsItem>
              <DescriptionsItem label="质保到期">{{ meterDetail.warranty_date }}</DescriptionsItem>
              <DescriptionsItem label="备注" :span="3">{{ meterDetail.notes || '-' }}</DescriptionsItem>
            </Descriptions>
          </TabPane>

          <TabPane key="comm" tab="通信配置">
            <template v-if="meterDetail.communication">
              <div style="margin-bottom: 12px; text-align: right">
                <Button type="primary" @click="openCommEditModal">编辑</Button>
              </div>
              <Descriptions :column="3" bordered size="middle">
                <DescriptionsItem label="连接类型">{{ meterDetail.communication.connection_type }}</DescriptionsItem>
                <DescriptionsItem label="地址">{{ meterDetail.communication.host }}:{{ meterDetail.communication.port }}</DescriptionsItem>
                <DescriptionsItem label="设备地址">{{ meterDetail.communication.device_address }}</DescriptionsItem>
                <DescriptionsItem label="波特率">{{ meterDetail.communication.baud_rate || '-' }}</DescriptionsItem>
                <DescriptionsItem label="超时时间">{{ meterDetail.communication.timeout }}秒</DescriptionsItem>
                <DescriptionsItem label="启用状态">
                  <Tag :color="meterDetail.communication.is_enabled ? 'green' : 'red'">{{ meterDetail.communication.is_enabled ? '已启用' : '已禁用' }}</Tag>
                </DescriptionsItem>
              </Descriptions>
            </template>
            <div v-else style="color: #999; text-align: center; padding: 40px">暂无通信配置</div>
          </TabPane>

          <TabPane key="snapshot" tab="实时状态">
            <template v-if="meterDetail.snapshot">
              <Row :gutter="16">
                <Col :span="8"><Card size="small"><Descriptions :column="1"><DescriptionsItem label="在线"><Tag :color="meterDetail.snapshot.online_status ? 'green' : 'red'">{{ meterDetail.snapshot.online_status ? '在线' : '离线' }}</Tag></DescriptionsItem><DescriptionsItem label="最后通信">{{ meterDetail.snapshot.last_comm_time || '-' }}</DescriptionsItem></Descriptions></Card></Col>
                <Col :span="8"><Card size="small"><Descriptions :column="1"><DescriptionsItem label="信号强度">{{ meterDetail.snapshot.signal_strength ?? '-' }}</DescriptionsItem><DescriptionsItem label="固件版本">{{ meterDetail.snapshot.firmware_version || '-' }}</DescriptionsItem></Descriptions></Card></Col>
                <Col :span="8"><Card size="small"><Descriptions :column="1"><DescriptionsItem label="堆栈使用">{{ meterDetail.snapshot.stack_usage ?? '-' }}%</DescriptionsItem><DescriptionsItem label="EEPROM写入">{{ meterDetail.snapshot.eeprom_write_count ?? '-' }}</DescriptionsItem></Descriptions></Card></Col>
              </Row>
            </template>
            <div v-else style="color: #999; text-align: center; padding: 40px">设备离线，无状态数据</div>
          </TabPane>

          <TabPane key="history" tab="状态变更记录">
            <Timeline>
              <TimelineItem v-for="h in statusHistory" :key="h.time" :color="h.to === '挂表测试中' ? 'blue' : h.to === '在库' ? 'green' : 'gray'">
                <div><Tag>{{ h.to }}</Tag> <span style="color: #999">{{ h.time }}</span></div>
                <div style="color: #666">{{ h.from }} → {{ h.to }}，操作人: {{ h.operator }}，原因: {{ h.reason }}</div>
              </TimelineItem>
            </Timeline>
          </TabPane>

          <TabPane key="attachments" tab="附件管理">
            <Table :columns="attachColumns" :data-source="attachments" row-key="id" :pagination="false" size="small">
              <template #bodyCell="{ column, record: _record }">
                <template v-if="column.key === 'action'">
                  <Button type="link" size="small">下载</Button>
                </template>
              </template>
            </Table>
            <div style="margin-top: 16px; text-align: center">
              <Upload :show-upload-list="false" accept=".jpg,.png,.pdf,.doc,.docx" :custom-request="handleUpload">
                <Button :loading="uploading">上传附件</Button>
              </Upload>
            </div>
          </TabPane>
        </Tabs>
      </Card>

      <BorrowDialog v-model:visible="showBorrowDialog" :meter-id="meterDetail.id" @success="fetchDetail" />
    </template>

    <!-- 编辑样机信息 Modal - PRD §3.1.4 -->
    <Modal v-model:open="showEditModal" title="编辑样机信息" @ok="handleEditSubmit" width="720px" :maskClosable="false" :confirmLoading="editLoading">
      <Form :model="editForm" layout="vertical" style="margin-top: 16px">
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="出厂编号" required><Input v-model:value="editForm.serial_number" placeholder="唯一标识" /></Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="表计名称" required><Input v-model:value="editForm.meter_name" placeholder="如: Coral测试表01" /></Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="表计类型" required>
              <Select v-model:value="editForm.meter_type_id" placeholder="选择表型"
                :options="meterTypes.map((t: any) => ({ value: t.id, label: `${t.name} (${t.code})` }))" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="所属项目" required>
              <Select v-model:value="editForm.project_id" placeholder="选择项目"
                :options="projects.map((p: any) => ({ value: p.id, label: p.name }))" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="通信协议" required>
              <Select v-model:value="editForm.protocol" :options="protocolOptions" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="线制类型">
              <Select v-model:value="editForm.line_type"
                :options="wireTypes.map((w: any) => ({ value: w.code, label: w.name }))" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="厂商"><Input v-model:value="editForm.manufacturer" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="型号"><Input v-model:value="editForm.model" placeholder="如: DCSP, DCPP" /></Form.Item></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="软件版本"><Input v-model:value="editForm.firmware_version" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="硬件版本"><Input v-model:value="editForm.hardware_version" /></Form.Item></Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12"><Form.Item label="框编号"><Input v-model:value="editForm.frame_number" /></Form.Item></Col>
          <Col :span="12"><Form.Item label="放置位置"><Input v-model:value="editForm.location" /></Form.Item></Col>
        </Row>
        <Form.Item label="备注"><Input.TextArea v-model:value="editForm.notes" :rows="2" /></Form.Item>
      </Form>
    </Modal>

    <!-- 编辑通信配置 Modal - PRD §5.2.3 -->
    <Modal v-model:open="showCommEditModal" title="编辑通信配置" @ok="handleCommEditSubmit" width="600px" :maskClosable="false" :confirmLoading="commLoading">
      <Form :model="commForm" layout="vertical" style="margin-top: 16px">
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="连接类型">
              <Select v-model:value="commForm.connection_type" :options="connectionTypeOptions" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="设备地址">
              <Input v-model:value="commForm.device_address" placeholder="如: 0012345678" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="主机地址">
              <Input v-model:value="commForm.host" placeholder="IP 或域名" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="端口">
              <InputNumber v-model:value="commForm.port" :min="1" :max="65535" style="width: 100%" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="波特率">
              <InputNumber v-model:value="commForm.baud_rate" :min="300" :max="115200" style="width: 100%" />
            </Form.Item>
          </Col>
          <Col :span="12">
            <Form.Item label="超时时间(秒)">
              <InputNumber v-model:value="commForm.timeout" :min="1" :max="300" style="width: 100%" />
            </Form.Item>
          </Col>
        </Row>
        <Row :gutter="16">
          <Col :span="12">
            <Form.Item label="启用状态">
              <Switch v-model:checked="commForm.is_enabled" checked-children="已启用" un-checked-children="已禁用" />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  </Page>
</template>
