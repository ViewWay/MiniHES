<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Badge, Button, Card, Col, Descriptions, DescriptionsItem, Modal, Progress, Row, Space, Statistic, Table, Tag, message } from 'ant-design-vue';
import { getTaskList, getTaskDetail } from '#/api/modules/task';
import { useWebSocket } from '#/composables/useWebSocket';

const router = useRouter();
const loading = ref(false);
const tasks = ref<any[]>([]);
let pollingTimer: ReturnType<typeof setInterval> | null = null;
const autoRefreshEnabled = ref(true);

// WebSocket integration
const { connect: wsConnect, subscribe: wsSubscribe, unsubscribe: wsUnsubscribe } = useWebSocket();

// Task detail modal
const detailModalVisible = ref(false);
const detailLoading = ref(false);
const taskDetail = ref<any>(null);

const taskStatusMap: Record<string, { color: string; text: string }> = {
  ready: { color: 'default', text: '就绪' },
  running: { color: 'blue', text: '执行中' },
  paused: { color: 'orange', text: '已暂停' },
  completed: { color: 'green', text: '已完成' },
  failed: { color: 'red', text: '失败' },
};

const taskTypeMap: Record<string, string> = { cron: '定时任务', interval: '循环任务', once: '一次性任务' };

const stats = computed(() => {
  const all = tasks.value;
  return {
    total: all.length,
    running: all.filter((t: any) => t.status === 'running').length,
    completed: all.filter((t: any) => t.status === 'completed').length,
    failed: all.filter((t: any) => t.status === 'failed').length,
    avgSuccessRate: all.length
      ? Math.round(all.reduce((sum: number, t: any) => sum + (t.success_rate || 0), 0) / all.length)
      : 0,
  };
});

const columns = [
  { title: '任务名称', dataIndex: 'task_name', width: 200, ellipsis: true },
  { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 110 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100, align: 'center' as const },
  { title: '设备数', dataIndex: 'total_devices', width: 80, align: 'center' as const },
  { title: '成功率', key: 'progress_rate', width: 160 },
  { title: '下次执行', dataIndex: 'next_execute_time', width: 170 },
  { title: '操作', key: 'action', width: 120, align: 'center' as const },
];

async function fetchData() {
  loading.value = true;
  try {
    const res = await getTaskList({ page: 1, page_size: 100 });
    tasks.value = res.items || [];
  } finally {
    loading.value = false;
  }
}

async function fetchTaskDetail(id: number) {
  detailModalVisible.value = true;
  detailLoading.value = true;
  try {
    const res = await getTaskDetail(id);
    taskDetail.value = res;
  } catch {
    taskDetail.value = null;
  } finally {
    detailLoading.value = false;
  }
}

function startPolling() {
  stopPolling();
  if (autoRefreshEnabled.value) {
    pollingTimer = setInterval(() => {
      fetchData();
    }, 5000);
  }
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

function toggleAutoRefresh() {
  autoRefreshEnabled.value = !autoRefreshEnabled.value;
  if (autoRefreshEnabled.value) {
    startPolling();
    message.success('已开启自动刷新（5秒间隔）');
  } else {
    stopPolling();
    message.info('已关闭自动刷新');
  }
}

function getProgressColor(rate: number): string {
  if (rate >= 95) return '#52c41a';
  if (rate >= 80) return '#faad14';
  return '#ff4d4f';
}

onMounted(() => {
  fetchData();
  startPolling();

  // WebSocket: connect and subscribe to task progress updates
  wsConnect();
  wsSubscribe('task:progress', (data: any) => {
    if (data?.task_id) {
      const index = tasks.value.findIndex((t: any) => t.id === data.task_id);
      if (index !== -1) {
        // Update task fields from WebSocket message
        tasks.value[index] = {
          ...tasks.value[index],
          status: data.status ?? tasks.value[index].status,
          success_rate: data.success_rate ?? tasks.value[index].success_rate,
          total_devices: data.total_devices ?? tasks.value[index].total_devices,
        };
      } else {
        // New task not in list — refresh from server
        fetchData();
      }
    }
  });
});

onUnmounted(() => {
  stopPolling();
  wsUnsubscribe('task:progress');
});
</script>

<template>
  <Page auto-content-height>
    <!-- Real-time Stats -->
    <Row :gutter="16" style="margin-bottom: 16px">
      <Col :span="5">
        <Card>
          <Statistic title="活跃任务" :value="stats.total" />
        </Card>
      </Col>
      <Col :span="5">
        <Card>
          <Statistic title="执行中" :value="stats.running" value-style="color: #1890ff">
            <template #prefix>
              <Badge status="processing" />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="5">
        <Card>
          <Statistic title="已完成" :value="stats.completed" value-style="color: #52c41a" />
        </Card>
      </Col>
      <Col :span="5">
        <Card>
          <Statistic title="失败" :value="stats.failed" value-style="color: #ff4d4f" />
        </Card>
      </Col>
      <Col :span="4">
        <Card>
          <Statistic title="平均成功率" :value="stats.avgSuccessRate" suffix="%">
            <template #formatter="{ value }">
              <span :style="{ color: getProgressColor(Number(value)) }">{{ value }}%</span>
            </template>
          </Statistic>
        </Card>
      </Col>
    </Row>

    <!-- Task Monitor Table -->
    <Card :bordered="false" title="任务监控" :loading="loading">
      <template #extra>
        <Space>
          <Button @click="toggleAutoRefresh" :type="autoRefreshEnabled ? 'primary' : 'default'" size="small">
            {{ autoRefreshEnabled ? '自动刷新: 开' : '自动刷新: 关' }}
          </Button>
          <Button @click="fetchData">手动刷新</Button>
          <Button @click="router.push('/task/list')">任务列表</Button>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="tasks"
        row-key="id"
        :pagination="false"
        :scroll="{ x: 950 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_type'">
            <Tag>{{ taskTypeMap[record.task_type] || record.task_type }}</Tag>
          </template>
          <template v-if="column.key === 'status'">
            <Tag :color="taskStatusMap[record.status]?.color">
              {{ taskStatusMap[record.status]?.text || record.status }}
            </Tag>
          </template>
          <template v-if="column.key === 'progress_rate'">
            <Progress
              :percent="record.success_rate || 0"
              :stroke-color="getProgressColor(record.success_rate || 0)"
              :size="'small'"
              :format="(percent: number) => `${percent}%`"
            />
          </template>
          <template v-if="column.key === 'action'">
            <Button type="link" size="small" @click="fetchTaskDetail(record.id)">
              详情
            </Button>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Task Detail Modal -->
    <Modal
      v-model:open="detailModalVisible"
      title="任务详情"
      width="700px"
      :footer="null"
      destroy-on-close
      :confirm-loading="detailLoading"
    >
      <template v-if="detailLoading">
        <Card loading style="min-height: 200px" />
      </template>
      <template v-else-if="taskDetail">
        <Descriptions bordered :column="2" size="small">
          <DescriptionsItem label="任务名称" :span="2">{{ taskDetail.task_name }}</DescriptionsItem>
          <DescriptionsItem label="任务类型">
            <Tag>{{ taskTypeMap[taskDetail.task_type] || taskDetail.task_type }}</Tag>
          </DescriptionsItem>
          <DescriptionsItem label="状态">
            <Tag :color="taskStatusMap[taskDetail.status]?.color">
              {{ taskStatusMap[taskDetail.status]?.text || taskDetail.status }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="优先级">{{ taskDetail.priority }}</DescriptionsItem>
          <DescriptionsItem label="超时(秒)">{{ taskDetail.timeout }}</DescriptionsItem>
          <DescriptionsItem label="重试次数">{{ taskDetail.retry_times }}</DescriptionsItem>
          <DescriptionsItem label="是否启用">
            <Tag :color="taskDetail.is_enabled ? 'green' : 'default'">
              {{ taskDetail.is_enabled ? '已启用' : '已禁用' }}
            </Tag>
          </DescriptionsItem>
          <DescriptionsItem label="设备数">{{ taskDetail.total_devices || 0 }}</DescriptionsItem>
          <DescriptionsItem label="成功率">
            <Progress
              :percent="taskDetail.success_rate || 0"
              :stroke-color="getProgressColor(taskDetail.success_rate || 0)"
              :size="'small'"
            />
          </DescriptionsItem>
          <DescriptionsItem label="最后执行" :span="2">
            {{ taskDetail.last_execute_time || '-' }}
          </DescriptionsItem>
          <DescriptionsItem label="下次执行" :span="2">
            {{ taskDetail.next_execute_time || '-' }}
          </DescriptionsItem>
        </Descriptions>
      </template>
      <template v-else>
        <Card>
          <Statistic title="无法加载任务详情" value="-" />
        </Card>
      </template>
    </Modal>
  </Page>
</template>
