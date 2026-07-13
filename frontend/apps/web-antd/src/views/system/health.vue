<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Badge,
  Button,
  Card,
  Col,
  Row,
  Spin,
  Statistic,
  Tag,
} from 'ant-design-vue';

import { getSystemHealth } from '#/api/modules/system';

interface ServiceStatus {
  name: string;
  status: 'offline' | 'online';
  last_check?: string;
}

const loading = ref(false);
const refreshing = ref(false);
const services = ref<ServiceStatus[]>([]);
const lastRefreshTime = ref('');

let pollTimer: ReturnType<typeof setInterval> | null = null;

const overallHealth = computed(() => {
  if (services.value.length === 0) return 'unknown';
  const allOnline = services.value.every((s) => s.status === 'online');
  if (allOnline) return 'green';
  return 'yellow';
});

const healthLabelMap: Record<string, string> = {
  green: '健康',
  yellow: '部分异常',
  red: '故障',
  unknown: '未知',
};

const serviceNameMap: Record<string, string> = {
  api: '后端 API',
  scheduler: '任务调度器',
  dlms_engine: 'DLMS 引擎',
  postgresql: 'PostgreSQL',
  mongodb: 'MongoDB',
  redis: 'Redis',
};

async function fetchData() {
  loading.value = true;
  try {
    const res = await getSystemHealth();
    const svcData = res?.services ?? {};
    services.value = Object.entries(svcData).map(
      ([key, val]: [string, any]) => ({
        name: key,
        status:
          val?.status === 'running' || val?.status === 'online'
            ? 'online'
            : 'offline',
        last_check: new Date().toISOString(),
      }),
    );
    lastRefreshTime.value = new Date().toLocaleString('zh-CN');
  } catch {
    services.value = [];
  } finally {
    loading.value = false;
  }
}

async function handleRefresh() {
  refreshing.value = true;
  await fetchData();
  refreshing.value = false;
}

onMounted(() => {
  fetchData();
  pollTimer = setInterval(fetchData, 15_000);
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" style="margin-bottom: 16px">
      <Row :gutter="16" align="middle">
        <Col :span="6">
          <Statistic
            title="系统状态"
            :value="healthLabelMap[overallHealth]"
            :value-style="{
              color:
                overallHealth === 'green'
                  ? '#52c41a'
                  : overallHealth === 'yellow'
                    ? '#faad14'
                    : '#ff4d4f',
            }"
          />
        </Col>
        <Col :span="6">
          <Statistic
            title="在线服务"
            :value="services.filter((s) => s.status === 'online').length"
            :suffix="`/ ${services.length}`"
          />
        </Col>
        <Col :span="6" style="text-align: center">
          <span style="color: #999; font-size: 12px">
            上次检查: {{ lastRefreshTime || '-' }}
          </span>
        </Col>
        <Col :span="6" style="text-align: right">
          <Button type="primary" :loading="refreshing" @click="handleRefresh">
            刷新
          </Button>
        </Col>
      </Row>
    </Card>

    <Spin :spinning="loading">
      <Row :gutter="16">
        <Col
          v-for="svc in services"
          :key="svc.name"
          :span="6"
          style="margin-bottom: 16px"
        >
          <Card :bordered="false">
            <div
              style="
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 12px;
              "
            >
              <Badge
                :status="svc.status === 'online' ? 'success' : 'error'"
              />
              <span style="font-weight: 600">
                {{ serviceNameMap[svc.name] || svc.name }}
              </span>
            </div>
            <Tag :color="svc.status === 'online' ? 'green' : 'red'">
              {{ svc.status === 'online' ? '在线' : '离线' }}
            </Tag>
          </Card>
        </Col>
      </Row>
      <Card v-if="services.length === 0 && !loading" :bordered="false">
        <div style="text-align: center; padding: 40px; color: #999">
          暂无服务状态数据，请检查后端连接
        </div>
      </Card>
    </Spin>
  </Page>
</template>
