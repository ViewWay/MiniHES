<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Page } from '@vben/common-ui';
import { Button, Card, Descriptions, DescriptionsItem, Table, Tag } from 'ant-design-vue';
import { getTestReport } from '#/api/modules/test';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const reportData = ref<any>(null);

const defectColumns = [
  { title: '缺陷ID', dataIndex: 'id', width: 80 },
  { title: '严重程度', dataIndex: 'severity', width: 100 },
  { title: '描述', dataIndex: 'description' },
  { title: '状态', dataIndex: 'status', width: 100 },
];

async function fetchReport() {
  const id = route.params.id;
  if (!id) return;
  loading.value = true;
  try { reportData.value = await getTestReport(Number(id)); }
  finally { loading.value = false; }
}

onMounted(() => { fetchReport(); });
</script>

<template>
  <Page auto-content-height>
    <div style="margin-bottom: 16px">
      <Button type="text" @click="router.push('/test/list')">返回列表</Button>
    </div>
    <template v-if="reportData">
      <Card :bordered="false" title="测试报告" style="margin-bottom: 16px">
        <template #extra>
          <Tag :color="reportData.conclusion === 'pass' ? 'green' : 'red'" style="font-size: 14px">
            {{ reportData.conclusion === 'pass' ? '通过' : '不通过' }}
          </Tag>
        </template>
        <Descriptions :column="2" bordered>
          <DescriptionsItem label="报告编号">{{ reportData.report_number }}</DescriptionsItem>
          <DescriptionsItem label="测试类型">{{ reportData.test_type }}</DescriptionsItem>
          <DescriptionsItem label="测试环境">{{ reportData.test_environment }}</DescriptionsItem>
          <DescriptionsItem label="挂测时长">{{ reportData.test_duration_days }}天</DescriptionsItem>
          <DescriptionsItem label="固件版本">{{ reportData.firmware_version }}</DescriptionsItem>
          <DescriptionsItem label="硬件版本">{{ reportData.hardware_version }}</DescriptionsItem>
        </Descriptions>
      </Card>
      <Card :bordered="false" title="缺陷列表">
        <Table :columns="defectColumns" :data-source="reportData.defects || []" row-key="id" :pagination="false" size="small">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === undefined && column.dataIndex === 'severity'">
              <Tag :color="record.severity === 'critical' ? 'red' : record.severity === 'major' ? 'orange' : 'blue'">{{ record.severity }}</Tag>
            </template>
            <template v-if="column.dataIndex === 'status'">
              <Tag :color="record.status === 'resolved' ? 'green' : 'orange'">{{ record.status }}</Tag>
            </template>
          </template>
        </Table>
      </Card>
    </template>
  </Page>
</template>
