<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import { onMounted, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Row,
  Select,
  Statistic,
  Table,
  Tag,
  message,
} from 'ant-design-vue';
import dayjs from 'dayjs';

import {
  exportDailyReport,
  getDailyAnalysis,
  getDailyMeters,
} from '#/api/modules/analysis';
import { getProjectList } from '#/api/modules/project';
import { useChartTheme } from '#/composables/useChartTheme';

const RangePicker = DatePicker.RangePicker;

const { themedAxis, themedTooltip, themedLegend, watchThemeAndRerender } =
  useChartTheme();

const loading = ref(false);
const exporting = ref(false);
const analysisData = ref<any>(null);

const selectedProject = ref<number | undefined>(undefined);
const selectedMeter = ref<number | undefined>(undefined);
const dateRange = ref<[dayjs.Dayjs, dayjs.Dayjs] | undefined>([
  dayjs().subtract(90, 'day'),
  dayjs(),
]);

const projectOptions = ref<{ label: string; value: number }[]>([]);
const meterOptions = ref<{ label: string; value: number }[]>([]);
const metersLoading = ref(false);

const energyChartRef = ref<EchartsUIType>();
const { renderEcharts: renderEnergyChart } = useEcharts(energyChartRef);

const cumulativeChartRef = ref<EchartsUIType>();
const { renderEcharts: renderCumulativeChart } = useEcharts(cumulativeChartRef);

watchThemeAndRerender(renderCharts);

async function fetchProjects() {
  try {
    const res = await getProjectList();
    const allProjects = res.items || res || [];
    projectOptions.value = allProjects.map((item: any) => ({
      label: item.name,
      value: item.id,
    }));
    // 自动选中第一个 DCPP 项目
    const dcppProject = allProjects.find(
      (p: any) =>
        p.name?.includes('DCPP') || p.name?.includes('DailyCheck'),
    );
    if (dcppProject) {
      selectedProject.value = dcppProject.id;
    }
  } catch (err) {
    console.error('[daily] fetchProjects failed', err);
  }
}

async function fetchMeters(projectId?: number) {
  metersLoading.value = true;
  selectedMeter.value = undefined;
  try {
    const res = await getDailyMeters(
      projectId ? { project_id: projectId } : undefined,
    );
    meterOptions.value = (res.items || []).map((m: any) => ({
      label: `${m.serial_number} - ${m.meter_name}`,
      value: m.id,
    }));
    if (meterOptions.value.length > 0 && meterOptions.value[0]) {
      selectedMeter.value = meterOptions.value[0].value;
      // 自动触发查询
      await handleSearch();
    }
  } catch (err) {
    console.error('[daily] fetchMeters failed', err);
    meterOptions.value = [];
  } finally {
    metersLoading.value = false;
  }
}

async function handleSearch() {
  if (!selectedMeter.value) {
    message.warning('请先选择设备');
    return;
  }
  loading.value = true;
  try {
    const [startDate, endDate] = dateRange.value || [];
    analysisData.value = await getDailyAnalysis({
      meter_id: selectedMeter.value,
      date_from: startDate?.format('YYYY-MM-DD') || '',
      date_to: endDate?.format('YYYY-MM-DD') || '',
    });
    renderCharts();
  } catch {
    message.error('查询失败');
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  const data = analysisData.value;
  if (!data || !data.energy_trend) return;

  const trend = data.energy_trend;

  renderEnergyChart({
    title: {
      text: '每日用电增量趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    grid: { top: 50, left: '3%', right: '4%', bottom: 10, containLabel: true },
    xAxis: themedAxis('x', {
      type: 'category',
      data: trend.labels || [],
      axisLabel: { rotate: 30 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: '增量' }),
    series: [
      {
        name: '日增量',
        type: 'bar',
        data: trend.increases || [],
        itemStyle: { color: '#5470c6' },
      },
    ],
  });

  renderCumulativeChart({
    title: {
      text: '累计电能趋势',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: themedTooltip({ trigger: 'axis' }),
    legend: themedLegend({ bottom: 0, data: ['累计电能'] }),
    grid: {
      top: 50,
      left: '3%',
      right: '4%',
      bottom: 40,
      containLabel: true,
    },
    xAxis: themedAxis('x', {
      type: 'category',
      boundaryGap: false,
      data: trend.labels || [],
      axisLabel: { rotate: 30 },
    }),
    yAxis: themedAxis('y', { type: 'value', name: 'kWh' }),
    series: [
      {
        name: '累计电能',
        type: 'line',
        smooth: true,
        data: trend.cumulative || [],
        itemStyle: { color: '#91cc75' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  });
}

async function handleExport() {
  if (!selectedMeter.value) {
    message.warning('请先选择设备');
    return;
  }
  exporting.value = true;
  try {
    const [startDate, endDate] = dateRange.value || [];
    const blob: Blob = await exportDailyReport({
      meter_id: selectedMeter.value,
      date_from: startDate?.format('YYYY-MM-DD') || '',
      date_to: endDate?.format('YYYY-MM-DD') || '',
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `日线分析_${selectedMeter.value}.csv`;
    document.body.append(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch {
    message.error('导出失败');
  } finally {
    exporting.value = false;
  }
}

const columns = [
  { title: '日期', dataIndex: 'date', width: 110 },
  { title: '累计电能', dataIndex: 'total_energy', width: 120 },
  { title: '日增量', dataIndex: 'daily_increase', width: 100 },
  { title: 'L1电压(V)', dataIndex: 'voltage_l1', width: 100 },
  { title: 'L1电流(A)', dataIndex: 'current_l1', width: 100 },
  { title: '总功率(W)', dataIndex: 'power_total', width: 100 },
  { title: '完整率', key: 'completeness', width: 90 },
  { title: '状态', key: 'status', width: 80 },
];

watch(selectedProject, (val) => {
  fetchMeters(val);
});

onMounted(() => {
  fetchProjects();
});
</script>

<template>
  <Page auto-content-height>
    <Card :bordered="false" title="每日数据分析" style="margin-bottom: 16px">
      <template #extra>
        <Button
          :loading="exporting"
          :disabled="!analysisData"
          @click="handleExport"
        >
          导出CSV
        </Button>
      </template>
      <Form layout="inline">
        <Form.Item label="项目">
          <Select
            v-model:value="selectedProject"
            allow-clear
            placeholder="全部项目"
            style="width: 200px"
            :options="projectOptions"
          />
        </Form.Item>
        <Form.Item label="设备">
          <Select
            v-model:value="selectedMeter"
            placeholder="选择设备"
            style="width: 220px"
            :options="meterOptions"
            :loading="metersLoading"
            show-search
            option-filter-prop="label"
          />
        </Form.Item>
        <Form.Item label="日期范围">
          <RangePicker
            v-model:value="dateRange"
            style="width: 260px"
            :presets="[
              {
                label: '近7天',
                value: [dayjs().subtract(7, 'day'), dayjs()],
              },
              {
                label: '近30天',
                value: [dayjs().subtract(30, 'day'), dayjs()],
              },
              {
                label: '近90天',
                value: [dayjs().subtract(90, 'day'), dayjs()],
              },
              {
                label: '近一年',
                value: [dayjs().subtract(1, 'year'), dayjs()],
              },
            ]"
          />
        </Form.Item>
        <Form.Item>
          <Button type="primary" :loading="loading" @click="handleSearch">
            查询分析
          </Button>
        </Form.Item>
      </Form>
    </Card>

    <template v-if="analysisData">
      <Card
        v-if="analysisData.summary?.demo"
        :bordered="false"
        style="margin-bottom: 16px"
        :body-style="{ padding: '8px 16px' }"
      >
        <Tag color="orange">无数据</Tag>
        <span style="margin-left: 8px; color: #999; font-size: 12px">
          该设备在所选日期范围内无采集数据
        </span>
      </Card>

      <Row
        v-if="!analysisData.summary?.demo"
        :gutter="16"
        style="margin-bottom: 16px"
      >
        <Col :span="6">
          <Card>
            <Statistic
              title="采集天数"
              :value="analysisData.summary?.days_collected"
              suffix="天"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="日均增量"
              :value="analysisData.summary?.avg_daily_increase"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="累计增量"
              :value="analysisData.summary?.total_increase"
            />
          </Card>
        </Col>
        <Col :span="6">
          <Card>
            <Statistic
              title="最新电能"
              :value="analysisData.summary?.latest_energy"
            />
          </Card>
        </Col>
      </Row>

      <Card
        v-if="!analysisData.summary?.demo"
        :bordered="false"
        title="每日用电增量趋势"
        style="margin-bottom: 16px"
      >
        <EchartsUI ref="energyChartRef" height="300px" />
      </Card>

      <Card
        v-if="!analysisData.summary?.demo"
        :bordered="false"
        title="累计电能趋势"
        style="margin-bottom: 16px"
      >
        <EchartsUI ref="cumulativeChartRef" height="300px" />
      </Card>

      <Card
        v-if="!analysisData.summary?.demo"
        :bordered="false"
        title="每日采集明细"
      >
        <Table
          :columns="columns"
          :data-source="analysisData.daily_records || []"
          row-key="date"
          size="middle"
          :pagination="{
            pageSize: 15,
            showTotal: (t: number) => `共 ${t} 条`,
          }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'completeness'">
              <Tag
                :color="
                  record.completeness >= 95
                    ? 'green'
                    : record.completeness >= 80
                      ? 'orange'
                      : 'red'
                "
              >
                {{ record.completeness }}%
              </Tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <Tag :color="record.status === 'success' ? 'green' : 'orange'">
                {{ record.status === 'success' ? '成功' : record.status }}
              </Tag>
            </template>
          </template>
        </Table>
      </Card>
    </template>

    <Card v-else :bordered="false">
      <div style="text-align: center; padding: 60px; color: #999">
        请选择项目和设备后点击「查询分析」
      </div>
    </Card>
  </Page>
</template>
