<script setup lang="ts">
import { ref, watch } from 'vue';
import {
  Form,
  Input,
  Select,
  DatePicker,
  Modal,
  message,
} from 'ant-design-vue';
import { borrowMeter } from '#/api/modules/meter';
import type { BorrowFormData } from '#/api/modules/meter';
import { getUserList } from '#/api/modules/system';

const props = defineProps<{ visible: boolean; meterId: number }>();
const emit = defineEmits<{ 'update:visible': [v: boolean]; success: [] }>();

interface UserOption {
  value: number;
  label: string;
}

const form = ref<BorrowFormData>({
  meter_id: props.meterId,
  borrower_name: '',
  expected_return_date: '',
  borrow_reason: '',
  department_approver: undefined,
});

const userOptions = ref<UserOption[]>([]);
const userFetching = ref(false);
const rules = {
  borrower_name: [{ required: true, message: '请选择借用人' }],
  expected_return_date: [{ required: true, message: '请选择预计归还日期' }],
  borrow_reason: [{ required: true, message: '请填写借用原因' }],
  department_approver: [{ required: true, message: '请选择部门审批人' }],
};

// Reset form when dialog opens
watch(
  () => props.visible,
  (val) => {
    if (val) {
      form.value = {
        meter_id: props.meterId,
        borrower_name: '',
        expected_return_date: '',
        borrow_reason: '',
        department_approver: undefined,
      };
      loadUsers();
    }
  },
);

// Load users for select
async function loadUsers(keyword?: string) {
  userFetching.value = true;
  try {
    const res = await getUserList({ page: 1, page_size: 50, keyword });
    const list = res?.items || res?.data || [];
    userOptions.value = (Array.isArray(list) ? list : []).map(
      (u: any) => ({
        value: u.id,
        label: u.name || u.username,
      }),
    );
  } catch {
    userOptions.value = [];
  } finally {
    userFetching.value = false;
  }
}

async function handleUserSearch(value: string) {
  await loadUsers(value);
}

async function handleSubmit() {
  if (!form.value.borrower_name) {
    message.warning('请选择借用人');
    return;
  }
  if (!form.value.expected_return_date) {
    message.warning('请选择预计归还日期');
    return;
  }
  if (!form.value.borrow_reason) {
    message.warning('请填写借用原因');
    return;
  }
  if (!form.value.department_approver) {
    message.warning('请选择部门审批人');
    return;
  }
  try {
    await borrowMeter(props.meterId, {
      ...form.value,
      meter_id: props.meterId,
    });
    message.success('借用申请已提交');
    emit('update:visible', false);
    emit('success');
  } catch {
    message.error('申请失败');
  }
}
</script>

<template>
  <Modal
    :open="visible"
    title="申请借用"
    @ok="handleSubmit"
    @cancel="emit('update:visible', false)"
    width="520px"
  >
    <Form
      :model="form"
      :rules="rules"
      layout="vertical"
      style="margin-top: 16px"
    >
      <Form.Item label="借用人" name="borrower_name" required>
        <Select
          v-model:value="form.borrower_name"
          show-search
          :filter-option="false"
          :loading="userFetching"
          placeholder="搜索并选择借用人"
          @search="handleUserSearch"
        >
          <Select.Option
            v-for="opt in userOptions"
            :key="opt.value"
            :value="opt.label"
          >
            {{ opt.label }}
          </Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="部门审批人" name="department_approver" required>
        <Select
          v-model:value="form.department_approver"
          show-search
          :filter-option="false"
          :loading="userFetching"
          placeholder="搜索并选择审批人"
          @search="handleUserSearch"
        >
          <Select.Option
            v-for="opt in userOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="预计归还日期" name="expected_return_date" required>
        <DatePicker
          v-model:value="form.expected_return_date"
          style="width: 100%"
          placeholder="选择预计归还日期"
        />
      </Form.Item>
      <Form.Item label="借用原因" name="borrow_reason" required>
        <Input.TextArea
          v-model:value="form.borrow_reason"
          :rows="3"
          placeholder="请说明借用原因"
        />
      </Form.Item>
    </Form>
  </Modal>
</template>
