<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button, Card, Cascader, Checkbox, Col, Descriptions, DescriptionsItem, Divider, Form, Input,
  InputNumber, message, Radio, RadioGroup, Row, Select, Space, Steps, Switch, Table, Tag,
} from 'ant-design-vue';
import { createTask } from '#/api/modules/task';
import type { TaskFormData } from '#/api/modules/task';
import { getProjectList, getMeterTypes, getWireTypes } from '#/api/modules/project';
import { getMeterList } from '#/api/modules/meter';

const router = useRouter();
const submitting = ref(false);
const currentStep = ref(0);

// Step 1: Basic info
const form = ref<TaskFormData>({
  task_name: '',
  task_type: 'interval',
  schedule_config: { interval: 120, unit: 'seconds' },
  execution_content: { action: 'read', points: ['1.0.0.0.0.255'] },
  filter_config: { project_id: undefined, meter_types: [], line_types: [], device_ids: [] },
  priority: 5,
  retry_times: 3,
  timeout: 300,
  is_enabled: true,
});

const taskTypeOptions = [
  { value: 'cron', label: '定时任务 (Cron表达式)' },
  { value: 'interval', label: '循环任务 (固定间隔)' },
  { value: 'once', label: '一次性任务 (执行后删除)' },
];

const actionOptions = [
  { value: 'read', label: '抄读整表' },
  { value: 'firmware', label: '固件升级' },
  { value: 'parameter', label: '参数下发' },
  { value: 'control', label: '控制命令' },
  { value: 'sts_recharge', label: 'STS/CTS充值' },
];

const obisOptions = [
  { value: '1.0.0.0.0.255', label: '总正向有功电能 (kWh)' },
  { value: '1.0.1.8.0.255', label: '当前需量 (W)' },
  { value: '1.0.12.7.0.255', label: '相位A电压 (V)' },
  { value: '1.0.21.7.0.255', label: '相位A电流 (A)' },
  { value: '1.0.0.2.0.255', label: '总正向无功电能 (kvarh)' },
  { value: '1.0.13.7.0.255', label: '相位B电压 (V)' },
  { value: '1.0.22.7.0.255', label: '相位B电流 (A)' },
  { value: '1.0.14.7.0.255', label: '相位C电压 (V)' },
  { value: '1.0.23.7.0.255', label: '相位C电流 (A)' },
  { value: '0.0.1.0.0.255', label: '电表状态' },
  { value: '0.0.96.1.0.255', label: '设备ID' },
];

// Step 2: Device filter - PRD §3.2.3 多维度筛选
const projects = ref<any[]>([]);
const meterTypes = ref<any[]>([]);
const wireTypes = ref<any[]>([]);
const deviceList = ref<any[]>([]);
const selectedDeviceIds = ref<number[]>([]);

const filterColumns = [
  { title: '选择', key: 'select', width: 60 },
  { title: '出厂编号', dataIndex: 'serial_number', width: 130 },
  { title: '名称', dataIndex: 'meter_name', width: 140 },
  { title: '项目', dataIndex: 'project_name', width: 120 },
  { title: '表型', dataIndex: 'meter_type', width: 80 },
  { title: '协议', dataIndex: 'protocol', width: 80 },
  { title: '状态', dataIndex: 'current_status', width: 100 },
];

const filteredDevices = computed(() => {
  let result = deviceList.value;
  const filter = form.value.filter_config as any;
  if (filter.project_id) result = result.filter((d: any) => d.project_id === filter.project_id);
  if (filter.meter_types?.length) result = result.filter((d: any) => filter.meter_types.includes(d.meter_type));
  if (filter.line_types?.length) result = result.filter((d: any) => filter.line_types.includes(d.line_type));
  return result;
});

function toggleDevice(id: number) {
  const idx = selectedDeviceIds.value.indexOf(id);
  if (idx >= 0) selectedDeviceIds.value.splice(idx, 1);
  else selectedDeviceIds.value.push(id);
}

function selectAll() {
  selectedDeviceIds.value = filteredDevices.value.map((d: any) => d.id);
}

function selectNone() {
  selectedDeviceIds.value = [];
}

async function fetchMetadata() {
  try {
    const [projRes, typeRes, wireRes] = await Promise.all([getProjectList(), getMeterTypes(), getWireTypes()]);
    projects.value = projRes.items || projRes || [];
    meterTypes.value = typeRes.items || typeRes || [];
    wireTypes.value = wireRes.items || wireRes || [];
  } catch { /* defaults */ }
  try {
    const devRes = await getMeterList({ page: 1, page_size: 500 });
    deviceList.value = devRes.items || [];
  } catch { /* defaults */ }
}

function nextStep() {
  if (currentStep.value === 0 && !form.value.task_name) {
    message.warning('请填写任务名称'); return;
  }
  currentStep.value++;
}

async function handleSubmit() {
  submitting.value = true;
  try {
    const data = {
      ...form.value,
      filter_config: {
        ...form.value.filter_config,
        device_ids: selectedDeviceIds.value,
      },
    };
    await createTask(data);
    message.success('任务创建成功');
    router.push('/task/list');
  } catch { message.error('创建失败'); }
  finally { submitting.value = false; }
}

fetchMetadata();
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false">
      <Steps :current="currentStep" style="margin-bottom: 24px">
        <Steps.Step title="基本配置" description="任务类型和调度" />
        <Steps.Step title="设备筛选" description="选择目标设备" />
        <Steps.Step title="执行内容" description="点位和参数" />
      </Steps>

      <!-- Step 1: Basic Config -->
      <template v-if="currentStep === 0">
        <Form :model="form" layout="vertical" style="max-width: 700px">
          <Form.Item label="任务名称" required><Input v-model:value="form.task_name" placeholder="如: Coral项目120秒采集" /></Form.Item>

          <Form.Item label="任务类型" required>
            <RadioGroup v-model:value="form.task_type">
              <Radio v-for="opt in taskTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</Radio>
            </RadioGroup>
          </Form.Item>

          <template v-if="form.task_type === 'interval'">
            <Form.Item label="执行间隔">
              <Space>
                <InputNumber v-model:value="(form.schedule_config as any).interval" :min="10" />
                <Select v-model:value="(form.schedule_config as any).unit" style="width: 100px"
                  :options="[{ value: 'seconds', label: '秒' }, { value: 'minutes', label: '分钟' }, { value: 'hours', label: '小时' }]" />
              </Space>
            </Form.Item>
          </template>
          <template v-if="form.task_type === 'cron'">
            <Form.Item label="Cron 表达式" help="格式: 秒 分 时 日 月 星期">
              <Input v-model:value="(form.schedule_config as any).cron" placeholder="0 30 2 * * ?（每天凌晨2:30）" />
            </Form.Item>
          </template>

          <Row :gutter="16">
            <Col :span="8"><Form.Item label="优先级 (1-10)"><InputNumber v-model:value="form.priority" :min="1" :max="10" style="width: 100%" /></Form.Item></Col>
            <Col :span="8"><Form.Item label="重试次数"><InputNumber v-model:value="form.retry_times" :min="0" :max="10" style="width: 100%" /></Form.Item></Col>
            <Col :span="8"><Form.Item label="超时(秒)"><InputNumber v-model:value="form.timeout" :min="10" style="width: 100%" /></Form.Item></Col>
          </Row>
          <Form.Item label="创建后立即启用"><Switch v-model:checked="form.is_enabled" /></Form.Item>
        </Form>
        <div style="text-align: right"><Button type="primary" @click="nextStep">下一步</Button></div>
      </template>

      <!-- Step 2: Device Filter - PRD §3.2.3 -->
      <template v-if="currentStep === 1">
        <Card size="small" title="筛选条件" style="margin-bottom: 16px">
          <Form layout="inline">
            <Form.Item label="项目">
              <Select v-model:value="(form.filter_config as any).project_id" allow-clear placeholder="全部项目" style="width: 180px"
                :options="projects.map((p: any) => ({ value: p.id, label: p.name }))" />
            </Form.Item>
            <Form.Item label="表型">
              <Select v-model:value="(form.filter_config as any).meter_types" mode="multiple" allow-clear placeholder="全部" style="width: 240px"
                :options="meterTypes.map((t: any) => ({ value: t.code, label: t.name }))" />
            </Form.Item>
            <Form.Item label="线制">
              <Select v-model:value="(form.filter_config as any).line_types" mode="multiple" allow-clear placeholder="全部" style="width: 200px"
                :options="wireTypes.map((w: any) => ({ value: w.code, label: w.name }))" />
            </Form.Item>
          </Form>
        </Card>

        <Space style="margin-bottom: 12px">
          <Button size="small" @click="selectAll">全选</Button>
          <Button size="small" @click="selectNone">清除</Button>
          <Tag>已选 {{ selectedDeviceIds.length }} 台设备</Tag>
        </Space>

        <Table :columns="filterColumns" :data-source="filteredDevices" row-key="id" :pagination="{ pageSize: 10 }" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'select'">
              <Checkbox :checked="selectedDeviceIds.includes(record.id)" @change="toggleDevice(record.id)" />
            </template>
            <template v-if="column.dataIndex === 'current_status'">
              <Tag :color="record.current_status === 'testing' ? 'blue' : 'green'" size="small">{{ record.current_status }}</Tag>
            </template>
          </template>
        </Table>

        <div style="text-align: right; margin-top: 16px">
          <Space>
            <Button @click="currentStep--">上一步</Button>
            <Button type="primary" @click="nextStep">下一步</Button>
          </Space>
        </div>
      </template>

      <!-- Step 3: Execution Content -->
      <template v-if="currentStep === 2">
        <Form :model="form" layout="vertical" style="max-width: 700px">
          <Form.Item label="执行操作" required>
            <Select v-model:value="(form.execution_content as any).action" :options="actionOptions" />
          </Form.Item>

          <Form.Item label="抄读点位 (OBIS码)">
            <Select v-model:value="(form.execution_content as any).points" mode="multiple" :options="obisOptions" placeholder="选择或搜索OBIS码" :showSearch="true" />
          </Form.Item>

          <Divider />

          <Form.Item label="任务确认">
            <Descriptions bordered :column="1" size="small">
              <DescriptionsItem label="任务名称">{{ form.task_name }}</DescriptionsItem>
              <DescriptionsItem label="类型">{{ taskTypeOptions.find(t => t.value === form.task_type)?.label }}</DescriptionsItem>
              <DescriptionsItem label="目标设备">{{ selectedDeviceIds.length }} 台</DescriptionsItem>
              <DescriptionsItem label="点位数">{{ (form.execution_content as any).points?.length || 0 }} 个</DescriptionsItem>
            </Descriptions>
          </Form.Item>
        </Form>

        <div style="text-align: right; margin-top: 16px">
          <Space>
            <Button @click="currentStep--">上一步</Button>
            <Button type="primary" @click="handleSubmit" :loading="submitting">创建任务</Button>
          </Space>
        </div>
      </template>
    </Card>
  </Page>
</template>
