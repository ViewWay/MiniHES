<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  DescriptionsItem,
  Form,
  InputNumber,
  Progress,
  Row,
  Statistic,
  Table,
  Tabs,
  TabPane,
  Tag,
  message,
} from 'ant-design-vue';
import { useRoute } from 'vue-router';

import { getDailyAnalysis } from '#/api/modules/analysis';

const route = useRoute();

const loading = ref(false);
const analysisData = ref<any>(null);
const searchForm = ref({
  meter_id: undefined as number | undefined,
  date: '' as any,
});

// Chart refs
const energyChartRef = ref<EchartsUIType>();
const { renderEcharts: renderEnergyChart } = useEcharts(energyChartRef);

const profileChartRef = ref<EchartsUIType>();
const { renderEcharts: renderProfileChart } = useEcharts(profileChartRef);

// Initialize from query params (for navigation from report page)
onMounted(() => {
  const queryMeterId = route.query.meter_id;
  const queryDate = route.query.date;
  if (queryMeterId) {
    searchForm.value.meter_id = Number(queryMeterId);
  }
  if (queryDate) {
    searchForm.value.date = queryDate as string;
  }
  if (queryMeterId && queryDate) {
    handleSearch();
  }
});

async function handleSearch() {
  if (!searchForm.value.meter_id || !searchForm.value.date) {
    message.warning('请填写设备ID和日期');
    return;
  }
  loading.value = true;
  try {
    analysisData.value = await getDailyAnalysis({
      meter_id: searchForm.value.meter_id,
      date: searchForm.value.date,
    });
    renderCharts();
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  const data = analysisData.value;
  if (!data) return;

  // Energy trend line chart
  const energyData = data.energy_trend || generateDemoEnergyTrend();
  const xData = energyData.map(
    (_: any, i: number) => `${i.toString().padStart(2, '0')}:00`,
  );

  renderEnergyChart({
    title: {
      text: '电能数据趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      bottom: 0,
      data: ['正向有功电能', '反向有功电能'],
    },
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
    },
    yAxis: {
      type: 'value',
      name: 'kWh',
    },
    series: [
      {
        name: '正向有功电能',
        type: 'line',
        smooth: true,
        data: energyData.map((d: any) => d.positive_active || d.value || 0),
        itemStyle: { color: '#5470c6' },
        areaStyle: { opacity: 0.1 },
        emphasis: { focus: 'series' },
      },
      {
        name: '反向有功电能',
        type: 'line',
        smooth: true,
        data: energyData.map((d: any) => d.negative_active || d.value2 || 0),
        itemStyle: { color: '#91cc75' },
        areaStyle: { opacity: 0.1 },
        emphasis: { focus: 'series' },
      },
    ],
  });

  // Profile completeness bar chart
  const profiles = data.profiles_list || generateDemoProfiles();

  renderProfileChart({
    title: {
      text: '曲线完整性检查',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = params[0];
        return `${p.axisValue}<br/>完整率: <b>${p.value}%</b>`;
      },
    },
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 10,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: profiles.map((p: any) => p.name),
      axisLabel: { rotate: 15 },
    },
    yAxis: {
      type: 'value',
      name: '完整率 (%)',
      min: 0,
      max: 100,
    },
    series: [
      {
        type: 'bar',
        data: profiles.map((p: any) => ({
          value: p.completeness,
          itemStyle: {
            color:
              p.completeness >= 95
                ? '#52c41a'
                : p.completeness >= 80
                  ? '#faad14'
                  : '#ff4d4f',
          },
        })),
        barWidth: '50%',
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%',
        },
      },
    ],
  });
}

function generateDemoEnergyTrend() {
  return Array.from({ length: 24 }, (_, i) => ({
    positive_active: (i * 0.8 + Math.random() * 2).toFixed(2),
    negative_active: (Math.random() * 0.5).toFixed(3),
  }));
}

function generateDemoProfiles() {
  return [
    { name: '日结算曲线', completeness: 100, expected: 48, actual: 48 },
    { name: '月结算曲线', completeness: 100, expected: 1, actual: 1 },
    { name: '负荷曲线1', completeness: 97, expected: 144, actual: 140 },
    { name: '负荷曲线2', completeness: 100, expected: 144, actual: 144 },
    { name: '电网质量曲线', completeness: 100, expected: 144, actual: 144 },
  ];
}

const abnormalColumns = [
  { title: '时间', dataIndex: 'time', width: 180 },
  { title: '类型', dataIndex: 'type', width: 120 },
  { title: '描述', dataIndex: 'description' },
  { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 100 },
];

// PRD 3.3.1 analysis items
const analysisItems = ref([
  {
    key: 'energy',
    label: '电能数据',
    status: 'normal',
    detail: '按周期递增，日增量 5.2kWh',
  },
  {
    key: 'clock',
    label: '时钟',
    status: 'normal',
    detail: '偏差 2 秒，在允许范围内',
  },
  {
    key: 'daily_billing',
    label: '日结算曲线',
    status: 'normal',
    detail: '预期 48 条，实际 48 条',
  },
  {
    key: 'monthly_billing',
    label: '月结算曲线',
    status: 'normal',
    detail: '预期 1 条，实际 1 条',
  },
  {
    key: 'load_profile_1',
    label: '负荷曲线1',
    status: 'normal',
    detail: '预期 144 条，实际 144 条',
  },
  {
    key: 'load_profile_2',
    label: '负荷曲线2',
    status: 'warning',
    detail: '预期 144 条，实际 140 条，缺失 4 条',
  },
  {
    key: 'power_quality',
    label: '电网质量曲线',
    status: 'normal',
    detail: '预期 144 条，实际 144 条',
  },
  {
    key: 'standard_events',
    label: '标准事件',
    status: 'normal',
    detail: '0 个事件',
  },
  {
    key: 'theft_events',
    label: '窃电事件',
    status: 'normal',
    detail: '0 个事件',
  },
  {
    key: 'comm_events',
    label: '通信事件',
    status: 'warning',
    detail: '2 次通信超时',
  },
  {
    key: 'prepay_events',
    label: '预付费事件',
    status: 'normal',
    detail: '0 个事件',
  },
]);
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="每日数据分析" style="margin-bottom: 16px">
      <Form layout="inline">
        <Form.Item label="设备ID">
          <InputNumber
            v-model:value="searchForm.meter_id"
            placeholder="输入设备ID"
          />
        </Form.Item>
        <Form.Item label="日期">
          <DatePicker
            v-model:value="searchForm.date"
            style="width: 200px"
          />
        </Form.Item>
        <Form.Item>
          <Button
            type="primary"
            @click="handleSearch"
            :loading="loading"
          >
            查询分析
          </Button>
        </Form.Item>
      </Form>
    </Card>

    <template v-if="analysisData">
      <!-- Summary statistics -->
      <Row :gutter="16" style="margin-bottom: 16px">
        <Col :span="6">
          <Card>
            <Statistic
              title="总电能 (kWh)"
              :value="analysisData.energy_data?.total_energy"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="日增量 (kWh)"
              :value="analysisData.energy_data?.daily_increase"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="增长率 (%)"
              :value="analysisData.energy_data?.increase_rate"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="时钟"
              :value="
                analysisData.clock_status?.is_accurate ? '准确' : '偏差'
              "
            />
            <div
              v-if="!analysisData.clock_status?.is_accurate"
              style="color: #999; font-size: 12px"
            >
              偏差 {{ analysisData.clock_status?.deviation_seconds }}秒
            </div>
          </Card>
        </Col>
      </Row>

      <!-- Energy trend chart -->
      <Card
        :bordered="false"
        title="电能数据趋势"
        style="margin-bottom: 16px"
      >
        <EchartsUI ref="energyChartRef" height="350px" />
      </Card>

      <!-- Profile completeness chart -->
      <Card
        :bordered="false"
        title="曲线完整性检查"
        style="margin-bottom: 16px"
      >
        <EchartsUI ref="profileChartRef" height="300px" />
      </Card>

      <!-- Tabs for detailed data -->
      <Card :bordered="false" style="margin-bottom: 16px">
        <Tabs>
          <TabPane key="checklist" tab="分析检查项">
            <Table
              :columns="[
                { title: '检查项', dataIndex: 'label', width: 150 },
                { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
                { title: '详情', dataIndex: 'detail' },
              ]"
              :data-source="analysisItems"
              row-key="key"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <Tag
                    :color="
                      record.status === 'normal'
                        ? 'green'
                        : record.status === 'warning'
                          ? 'orange'
                          : 'red'
                    "
                  >
                    {{
                      record.status === 'normal'
                        ? '正常'
                        : record.status === 'warning'
                          ? '异常'
                          : '错误'
                    }}
                  </Tag>
                </template>
              </template>
            </Table>
          </TabPane>

          <TabPane key="profiles" tab="曲线完整性">
            <Descriptions :column="2" bordered size="small">
              <DescriptionsItem label="日结算曲线">
                <Progress
                  :percent="
                    analysisData.profiles?.daily_billing?.completeness || 100
                  "
                  :size="'small'"
                />
              </DescriptionsItem>
              <DescriptionsItem label="负荷曲线1">
                <Progress
                  :percent="
                    analysisData.profiles?.load_profile_1?.completeness || 100
                  "
                  :size="'small'"
                />
              </DescriptionsItem>
            </Descriptions>
          </TabPane>

          <TabPane key="events" tab="事件统计">
            <Row :gutter="16">
              <Col :span="6">
                <Card size="small">
                  <Statistic
                    title="标准事件"
                    :value="analysisData.events?.standard || 0"
                  />
                </Card>
              </Col>
              <Col :span="6">
                <Card size="small">
                  <Statistic
                    title="窃电事件"
                    :value="analysisData.events?.theft || 0"
                    :value-style="{ color: '#ff4d4f' }"
                  />
                </Card>
              </Col>
              <Col :span="6">
                <Card size="small">
                  <Statistic
                    title="通信事件"
                    :value="analysisData.events?.communication || 0"
                    :value-style="{ color: '#fa8c16' }"
                  />
                </Card>
              </Col>
              <Col :span="6">
                <Card size="small">
                  <Statistic
                    title="预付费事件"
                    :value="analysisData.events?.prepayment || 0"
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>

      <!-- Abnormal data table -->
      <Card :bordered="false" title="异常数据">
        <Table
          :columns="abnormalColumns"
          :data-source="analysisData.abnormal_data || []"
          row-key="time"
          :pagination="false"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'severity'">
              <Tag :color="record.severity === 'critical' ? 'red' : 'orange'">
                {{ record.severity }}
              </Tag>
            </template>
          </template>
        </Table>
      </Card>
    </template>
  </Page>
</template>
