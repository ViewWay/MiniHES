<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import {
  Button,
  Card,
  Checkbox,
  CheckboxGroup,
  Descriptions,
  DescriptionsItem,
  Form,
  FormItem,
  Input,
  Modal,
  Select,
  SelectOption,
  Space,
  Spin,
  Table,
  Tag,
  Textarea,
  message,
} from 'ant-design-vue';
import {
  getTestReport,
  exportTestReport,
  distributeReport,
  updateTestReport,
} from '#/api/modules/test';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const exporting = ref(false);
const reportData = ref<any>(null);
const reportStatus = ref<'draft' | 'published'>('draft');

// Distribute modal
const showDistributeModal = ref(false);
const distributing = ref(false);
const distributeForm = ref<{ recipients: string[]; message: string }>({
  recipients: [],
  message: '',
});

const recipientOptions = [
  { label: '项目软件测试负责人', value: 'project_test_lead' },
  { label: '项目研发负责人', value: 'project_dev_lead' },
  { label: '功能测试负责人', value: 'feature_test_lead' },
  { label: '功能研发负责人', value: 'feature_dev_lead' },
  { label: '测试领导', value: 'test_manager' },
  { label: '研发领导', value: 'dev_manager' },
  { label: '部门', value: 'department' },
];

// Edit modal
const showEditModal = ref(false);
const editSubmitting = ref(false);
const editForm = ref<any>({});

const defectColumns = [
  { title: '缺陷ID', dataIndex: 'id', width: 80 },
  { title: '严重程度', dataIndex: 'severity', width: 100 },
  { title: '描述', dataIndex: 'description' },
  { title: '状态', dataIndex: 'status', width: 100 },
];

const statusColor = computed(() =>
  reportStatus.value === 'published' ? 'green' : 'orange',
);
const statusText = computed(() =>
  reportStatus.value === 'published' ? '已发布' : '草稿',
);

async function fetchReport() {
  const id = route.params.id;
  if (!id) return;
  loading.value = true;
  try {
    reportData.value = await getTestReport(Number(id));
    reportStatus.value = reportData.value.status || 'draft';
  } finally {
    loading.value = false;
  }
}

async function handleExportPDF() {
  const id = Number(route.params.id);
  if (!id) return;
  exporting.value = true;
  try {
    const blob = await exportTestReport(id);
    const url = window.URL.createObjectURL(
      blob instanceof Blob ? blob : new Blob([blob]),
    );
    const link = document.createElement('a');
    link.href = url;
    link.download = `test-report-${id}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    message.success('PDF导出成功');
  } catch {
    message.error('导出失败');
  } finally {
    exporting.value = false;
  }
}

function openDistributeModal() {
  distributeForm.value = { recipients: [], message: '' };
  showDistributeModal.value = true;
}

async function handleDistribute() {
  if (distributeForm.value.recipients.length === 0) {
    message.warning('请至少选择一个收件人');
    return;
  }
  distributing.value = true;
  try {
    await distributeReport(Number(route.params.id), distributeForm.value);
    message.success('邮件已发送');
    showDistributeModal.value = false;
  } catch {
    message.error('发送失败');
  } finally {
    distributing.value = false;
  }
}

function openEditModal() {
  if (!reportData.value) return;
  editForm.value = {
    test_type: reportData.value.test_type || '',
    test_environment: reportData.value.test_environment || '',
    test_duration_days: reportData.value.test_duration_days || 0,
    firmware_version: reportData.value.firmware_version || '',
    hardware_version: reportData.value.hardware_version || '',
    conclusion: reportData.value.conclusion || 'pass',
    notes: reportData.value.notes || '',
  };
  showEditModal.value = true;
}

async function handleEditSubmit() {
  editSubmitting.value = true;
  try {
    await updateTestReport(Number(route.params.id), editForm.value);
    message.success('报告已更新');
    showEditModal.value = false;
    fetchReport();
  } catch {
    message.error('更新失败');
  } finally {
    editSubmitting.value = false;
  }
}

onMounted(() => {
  fetchReport();
});
</script>

<template>
  <Page auto-content-height>
    <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center">
      <Button type="text" @click="router.push('/test/list')">返回列表</Button>
      <Space v-if="reportData">
        <Tag :color="statusColor" style="font-size: 14px; padding: 2px 12px">
          {{ statusText }}
        </Tag>
        <Button @click="openEditModal">编辑报告</Button>
        <Button @click="openDistributeModal">发送邮件</Button>
        <Button type="primary" :loading="exporting" @click="handleExportPDF">
          导出PDF
        </Button>
      </Space>
    </div>

    <Spin :spinning="loading">
      <template v-if="reportData">
        <Card :bordered="false" title="测试报告" style="margin-bottom: 16px">
          <template #extra>
            <Tag
              :color="reportData.conclusion === 'pass' ? 'green' : 'red'"
              style="font-size: 14px"
            >
              {{ reportData.conclusion === 'pass' ? '通过' : '不通过' }}
            </Tag>
          </template>
          <Descriptions :column="2" bordered>
            <DescriptionsItem label="报告编号">
              {{ reportData.report_number }}
            </DescriptionsItem>
            <DescriptionsItem label="测试类型">
              {{ reportData.test_type }}
            </DescriptionsItem>
            <DescriptionsItem label="测试环境">
              {{ reportData.test_environment }}
            </DescriptionsItem>
            <DescriptionsItem label="挂测时长">
              {{ reportData.test_duration_days }}天
            </DescriptionsItem>
            <DescriptionsItem label="固件版本">
              {{ reportData.firmware_version }}
            </DescriptionsItem>
            <DescriptionsItem label="硬件版本">
              {{ reportData.hardware_version }}
            </DescriptionsItem>
          </Descriptions>
        </Card>

        <Card :bordered="false" title="缺陷列表" style="margin-bottom: 16px">
          <Table
            :columns="defectColumns"
            :data-source="reportData.defects || []"
            row-key="id"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template
                v-if="column.key === undefined && column.dataIndex === 'severity'"
              >
                <Tag
                  :color="
                    record.severity === 'critical'
                      ? 'red'
                      : record.severity === 'major'
                        ? 'orange'
                        : 'blue'
                  "
                >
                  {{ record.severity }}
                </Tag>
              </template>
              <template v-if="column.dataIndex === 'status'">
                <Tag :color="record.status === 'resolved' ? 'green' : 'orange'">
                  {{ record.status }}
                </Tag>
              </template>
            </template>
          </Table>
        </Card>

        <Card
          v-if="reportData.notes"
          :bordered="false"
          title="备注"
        >
          <div style="white-space: pre-wrap">{{ reportData.notes }}</div>
        </Card>
      </template>
    </Spin>

    <!-- Distribute email modal -->
    <Modal
      v-model:open="showDistributeModal"
      title="发送邮件"
      :confirm-loading="distributing"
      @ok="handleDistribute"
      width="520px"
    >
      <Form layout="vertical" style="margin-top: 16px">
        <FormItem label="收件人" required>
          <CheckboxGroup
            v-model:value="distributeForm.recipients"
            style="display: flex; flex-direction: column; gap: 8px"
          >
            <Checkbox
              v-for="opt in recipientOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </Checkbox>
          </CheckboxGroup>
        </FormItem>
        <FormItem label="附言">
          <Textarea
            v-model:value="distributeForm.message"
            :rows="4"
            placeholder="可选，输入邮件附言"
          />
        </FormItem>
      </Form>
    </Modal>

    <!-- Edit report modal -->
    <Modal
      v-model:open="showEditModal"
      title="编辑测试报告"
      :confirm-loading="editSubmitting"
      @ok="handleEditSubmit"
      width="600px"
    >
      <Form :model="editForm" layout="vertical" style="margin-top: 16px">
        <FormItem label="测试类型" required>
          <Select v-model:value="editForm.test_type" placeholder="选择测试类型">
            <SelectOption value="type_test">型式试验</SelectOption>
            <SelectOption value="routine_test">例行试验</SelectOption>
            <SelectOption value="acceptance_test">验收试验</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="测试环境" required>
          <Input v-model:value="editForm.test_environment" />
        </FormItem>
        <FormItem label="挂测时长(天)" required>
          <Input v-model:value="editForm.test_duration_days" type="number" />
        </FormItem>
        <FormItem label="固件版本" required>
          <Input v-model:value="editForm.firmware_version" />
        </FormItem>
        <FormItem label="硬件版本" required>
          <Input v-model:value="editForm.hardware_version" />
        </FormItem>
        <FormItem label="测试结论" required>
          <Select v-model:value="editForm.conclusion">
            <SelectOption value="pass">通过</SelectOption>
            <SelectOption value="fail">不通过</SelectOption>
          </Select>
        </FormItem>
        <FormItem label="备注">
          <Textarea v-model:value="editForm.notes" :rows="3" />
        </FormItem>
      </Form>
    </Modal>
  </Page>
</template>
