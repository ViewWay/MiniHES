<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Page } from '@vben/common-ui';
import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
  InputNumber,
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
  getMeterPoints,
  createMeterPoint,
  updateMeterPoint,
  deleteMeterPoint,
} from '#/api/modules/project';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Modal state
const showModal = ref(false);
const modalTitle = ref('新增采集点');
const editingId = ref<number | null>(null);
const submitting = ref(false);

const formState = ref({
  point_code: '',
  point_name: '',
  point_type: 'register',
  data_type: '',
  unit: '',
  protocol: 'dlms',
  storage_target: 'influxdb',
  retention_days: 365,
});

const pointTypeOptions = [
  { label: '寄存器', value: 'register' },
  { label: '属性', value: 'attribute' },
  { label: '曲线', value: 'profile' },
];

const protocolOptions = [
  { label: 'DLMS/COSEM', value: 'dlms' },
  { label: 'Modbus', value: 'modbus' },
  { label: 'IEC 62056-21', value: 'iec62056' },
];

const storageOptions = [
  { label: 'InfluxDB', value: 'influxdb' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'TimescaleDB', value: 'timescaledb' },
];

const pointTypeColorMap: Record<string, string> = {
  register: 'blue',
  attribute: 'green',
  profile: 'purple',
};

function formatPointType(type: string) {
  const map: Record<string, string> = {
    register: '寄存器',
    attribute: '属性',
    profile: '曲线',
  };
  return map[type] || type;
}

const columns = [
  { title: '点号(OBIS)', dataIndex: 'point_code', width: 160 },
  { title: '点名', dataIndex: 'point_name', width: 150 },
  { title: '类型', dataIndex: 'point_type', key: 'point_type', width: 100 },
  { title: '数据类型', dataIndex: 'data_type', width: 100 },
  { title: '单位', dataIndex: 'unit', width: 80 },
  { title: '协议', dataIndex: 'protocol', width: 120 },
  { title: '存储目标', dataIndex: 'storage_target', width: 120 },
  { title: '保留天数', dataIndex: 'retention_days', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getMeterPoints();
    tableData.value = res.items || res || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  modalTitle.value = '新增采集点';
  formState.value = {
    point_code: '',
    point_name: '',
    point_type: 'register',
    data_type: '',
    unit: '',
    protocol: 'dlms',
    storage_target: 'influxdb',
    retention_days: 365,
  };
  showModal.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  modalTitle.value = '编辑采集点';
  formState.value = {
    point_code: record.point_code || '',
    point_name: record.point_name || '',
    point_type: record.point_type || 'register',
    data_type: record.data_type || '',
    unit: record.unit || '',
    protocol: record.protocol || 'dlms',
    storage_target: record.storage_target || 'influxdb',
    retention_days: record.retention_days || 365,
  };
  showModal.value = true;
}

async function handleSubmit() {
  if (!formState.value.point_code) {
    message.warning('请填写点号');
    return;
  }
  if (!formState.value.point_name) {
    message.warning('请填写点名');
    return;
  }
  submitting.value = true;
  try {
    const payload: any = { ...formState.value };
    if (editingId.value) {
      await updateMeterPoint(editingId.value, payload);
      message.success('更新成功');
    } else {
      await createMeterPoint(payload);
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
    await deleteMeterPoint(id);
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
    <Card :bordered="false" title="采集点配置">
      <template #extra>
        <Space>
          <Button type="primary" @click="openCreate">新增采集点</Button>
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
        }"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'point_type'">
            <Tag :color="pointTypeColorMap[record.point_type] || 'default'">
              {{ formatPointType(record.point_type) }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">
                编辑
              </Button>
              <Popconfirm
                title="确认删除该采集点？"
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
      width="600px"
    >
      <Form :model="formState" layout="vertical" style="margin-top: 16px">
        <FormItem label="点号(OBIS码)" required>
          <Input
            v-model:value="formState.point_code"
            placeholder="例如: 1.0.0.0.0.255"
          />
        </FormItem>
        <FormItem label="点名" required>
          <Input
            v-model:value="formState.point_name"
            placeholder="输入采集点名称"
          />
        </FormItem>
        <FormItem label="类型">
          <Select v-model:value="formState.point_type">
            <SelectOption
              v-for="opt in pointTypeOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="数据类型">
          <Input
            v-model:value="formState.data_type"
            placeholder="例如: float32, uint32, string"
          />
        </FormItem>
        <FormItem label="单位">
          <Input
            v-model:value="formState.unit"
            placeholder="例如: kWh, V, A, W"
          />
        </FormItem>
        <FormItem label="协议">
          <Select v-model:value="formState.protocol">
            <SelectOption
              v-for="opt in protocolOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="存储目标">
          <Select v-model:value="formState.storage_target">
            <SelectOption
              v-for="opt in storageOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="保留天数">
          <InputNumber
            v-model:value="formState.retention_days"
            :min="1"
            :max="3650"
            style="width: 100%"
            placeholder="数据保留天数"
          />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
