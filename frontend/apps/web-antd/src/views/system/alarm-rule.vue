<script setup lang="ts">
import { ref, onMounted } from 'vue';
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
  Switch,
  Table,
  Tag,
  Textarea,
  message,
} from 'ant-design-vue';
import {
  getAlarmRules,
  createAlarmRule,
  updateAlarmRule,
  deleteAlarmRule,
} from '#/api/modules/alarm';

const loading = ref(false);
const tableData = ref<any[]>([]);
const total = ref(0);
const pagination = ref({ current: 1, pageSize: 20 });

// Modal state
const showModal = ref(false);
const modalTitle = ref('新建告警规则');
const editingId = ref<number | null>(null);
const submitting = ref(false);

const formState = ref({
  rule_name: '',
  rule_type: 'threshold',
  point_code: '',
  condition_config: '',
  severity: 'warning',
  is_enabled: true,
});

const ruleTypeOptions = [
  { label: '阈值告警', value: 'threshold' },
  { label: '异常检测', value: 'anomaly' },
  { label: '通信告警', value: 'communication' },
];

const obisOptions = [
  { label: '1.0.0.0.0.255 - 总正向有功电能 (kWh)', value: '1.0.0.0.0.255' },
  { label: '1.0.1.8.0.255 - 当前需量 (W)', value: '1.0.1.8.0.255' },
  { label: '1.0.12.7.0.255 - 相位A电压 (V)', value: '1.0.12.7.0.255' },
  { label: '1.0.21.7.0.255 - 相位A电流 (A)', value: '1.0.21.7.0.255' },
  { label: '0.0.1.0.0.255 - 电表状态', value: '0.0.1.0.0.255' },
];

const severityOptions = [
  { label: '严重', value: 'critical' },
  { label: '警告', value: 'warning' },
  { label: '信息', value: 'info' },
];

const severityColorMap: Record<string, string> = {
  critical: 'red',
  warning: 'orange',
  info: 'blue',
};

const columns = [
  { title: '规则名称', dataIndex: 'rule_name', width: 160 },
  { title: '规则类型', dataIndex: 'rule_type', key: 'rule_type', width: 120 },
  { title: '监测点(OBIS)', dataIndex: 'point_code', width: 180 },
  { title: '条件配置', dataIndex: 'condition_config', ellipsis: true },
  { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 100 },
  { title: '状态', dataIndex: 'is_enabled', key: 'is_enabled', width: 80 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getAlarmRules({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  modalTitle.value = '新建告警规则';
  formState.value = {
    rule_name: '',
    rule_type: 'threshold',
    point_code: '',
    condition_config: '',
    severity: 'warning',
    is_enabled: true,
  };
  showModal.value = true;
}

function openEdit(record: any) {
  editingId.value = record.id;
  modalTitle.value = '编辑告警规则';
  formState.value = {
    rule_name: record.rule_name || '',
    rule_type: record.rule_type || 'threshold',
    point_code: record.point_code || '',
    condition_config:
      typeof record.condition_config === 'object'
        ? JSON.stringify(record.condition_config, null, 2)
        : record.condition_config || '',
    severity: record.severity || 'warning',
    is_enabled: record.is_enabled !== false,
  };
  showModal.value = true;
}

async function handleSubmit() {
  if (!formState.value.rule_name) {
    message.warning('请填写规则名称');
    return;
  }
  submitting.value = true;
  try {
    const payload: any = { ...formState.value };
    // Parse condition_config as JSON if valid
    if (typeof payload.condition_config === 'string' && payload.condition_config.trim()) {
      try {
        payload.condition_config = JSON.parse(payload.condition_config);
      } catch {
        // keep as string if not valid JSON
      }
    }
    if (editingId.value) {
      await updateAlarmRule(editingId.value, payload);
      message.success('更新成功');
    } else {
      await createAlarmRule(payload);
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
    await deleteAlarmRule(id);
    message.success('已删除');
    fetchData();
  } catch {
    message.error('删除失败');
  }
}

async function handleToggleEnabled(record: any) {
  try {
    await updateAlarmRule(record.id, {
      is_enabled: !record.is_enabled,
    });
    message.success(record.is_enabled ? '已禁用' : '已启用');
    fetchData();
  } catch {
    message.error('操作失败');
  }
}

function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  fetchData();
}

function formatRuleType(type: string) {
  const map: Record<string, string> = {
    threshold: '阈值告警',
    anomaly: '异常检测',
    communication: '通信告警',
  };
  return map[type] || type;
}

function formatSeverity(severity: string) {
  const map: Record<string, string> = {
    critical: '严重',
    warning: '警告',
    info: '信息',
  };
  return map[severity] || severity;
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="告警规则配置">
      <template #extra>
        <Space>
          <Button type="primary" @click="openCreate">新建规则</Button>
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
          <template v-if="column.key === 'rule_type'">
            <Tag>{{ formatRuleType(record.rule_type) }}</Tag>
          </template>
          <template v-if="column.key === 'severity'">
            <Tag :color="severityColorMap[record.severity] || 'default'">
              {{ formatSeverity(record.severity) }}
            </Tag>
          </template>
          <template v-if="column.key === 'is_enabled'">
            <Switch
              :checked="record.is_enabled"
              @change="handleToggleEnabled(record)"
              checked-children="启用"
              un-checked-children="禁用"
            />
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="openEdit(record)">
                编辑
              </Button>
              <Popconfirm
                title="确认删除该规则？"
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
        <FormItem label="规则名称" required>
          <Input
            v-model:value="formState.rule_name"
            placeholder="输入规则名称"
          />
        </FormItem>
        <FormItem label="规则类型" required>
          <Select v-model:value="formState.rule_type">
            <SelectOption
              v-for="opt in ruleTypeOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="监测点(OBIS码)">
          <Select
            v-model:value="formState.point_code"
            placeholder="选择OBIS码"
            allow-clear
          >
            <SelectOption
              v-for="opt in obisOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="条件配置">
          <Textarea
            v-model:value="formState.condition_config"
            :rows="4"
            placeholder='输入JSON格式条件，例如：{"operator": ">", "value": 100}'
          />
        </FormItem>
        <FormItem label="严重程度" required>
          <Select v-model:value="formState.severity">
            <SelectOption
              v-for="opt in severityOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </SelectOption>
          </Select>
        </FormItem>
        <FormItem label="启用状态">
          <Switch
            v-model:checked="formState.is_enabled"
            checked-children="启用"
            un-checked-children="禁用"
          />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
