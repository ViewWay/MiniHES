import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:bar-chart-3',
      title: '数据分析',
      order: 3,
    },
    name: 'Analysis',
    path: '/analysis',
    children: [
      // ── 基础分析 ──
      {
        name: 'AnalysisBasic',
        path: '/analysis/basic',
        meta: {
          icon: 'lucide:layout-grid',
          title: '基础分析',
        },
        children: [
          {
            name: 'AnalysisDaily',
            path: '/analysis/daily',
            component: () => import('#/views/analysis/daily.vue'),
            meta: {
              icon: 'lucide:calendar',
              title: '每日分析',
            },
          },
          {
            name: 'AnalysisCompare',
            path: '/analysis/compare',
            component: () => import('#/views/analysis/compare.vue'),
            meta: {
              icon: 'lucide:git-compare',
              title: '对比分析',
            },
          },
          {
            name: 'AnalysisReport',
            path: '/analysis/report',
            component: () => import('#/views/analysis/report.vue'),
            meta: {
              icon: 'lucide:file-bar-chart',
              title: '分析报告',
            },
          },
          {
            name: 'Consistency',
            path: '/analysis/consistency',
            component: () => import('#/views/analysis/consistency.vue'),
            meta: {
              icon: 'lucide:check-circle-2',
              title: '一致性检查',
            },
          },
          {
            name: 'DataQuality',
            path: '/analysis/data-quality',
            component: () => import('#/views/analysis/data-quality.vue'),
            meta: {
              icon: 'lucide:shield-check',
              title: '数据质量',
            },
          },
        ],
      },
      // ── 通信与抄表 ──
      {
        name: 'AnalysisComm',
        path: '/analysis/comm',
        meta: {
          icon: 'lucide:radio-tower',
          title: '通信与抄表',
        },
        children: [
          {
            name: 'CommSuccessRate',
            path: '/analysis/comm-success-rate',
            component: () => import('#/views/analysis/comm-success-rate.vue'),
            meta: {
              icon: 'lucide:activity',
              title: '通信成功率',
            },
          },
          {
            name: 'NonCommDevices',
            path: '/analysis/non-comm-devices',
            component: () => import('#/views/analysis/non-comm-devices.vue'),
            meta: {
              icon: 'lucide:wifi-off',
              title: '未通信设备',
            },
          },
          {
            name: 'ReadCompleteness',
            path: '/analysis/read-completeness',
            component: () => import('#/views/analysis/read-completeness.vue'),
            meta: {
              icon: 'lucide:check-square',
              title: '抄表完整率',
            },
          },
          {
            name: 'RetryAnalysis',
            path: '/analysis/retry-analysis',
            component: () => import('#/views/analysis/retry-analysis.vue'),
            meta: {
              icon: 'lucide:rotate-cw',
              title: '重试分析',
            },
          },
          {
            name: 'OndemandHistory',
            path: '/analysis/ondemand-history',
            component: () => import('#/views/analysis/ondemand-history.vue'),
            meta: {
              icon: 'lucide:hand',
              title: '按需抄表',
            },
          },
        ],
      },
      // ── 告警与诊断 ──
      {
        name: 'AnalysisAlarm',
        path: '/analysis/alarm',
        meta: {
          icon: 'lucide:bell',
          title: '告警与诊断',
        },
        children: [
          {
            name: 'OpenAlarmsReport',
            path: '/analysis/open-alarms-report',
            component: () => import('#/views/analysis/open-alarms-report.vue'),
            meta: {
              icon: 'lucide:bell-ring',
              title: '未确认告警',
            },
          },
          {
            name: 'AlarmTrend',
            path: '/analysis/alarm-trend',
            component: () => import('#/views/analysis/alarm-trend.vue'),
            meta: {
              icon: 'lucide:trending-up',
              title: '告警趋势',
            },
          },
          {
            name: 'DeviceHealth',
            path: '/analysis/device-health',
            component: () => import('#/views/analysis/device-health.vue'),
            meta: {
              icon: 'lucide:heart-pulse',
              title: '设备健康',
            },
          },
          {
            name: 'SignalAging',
            path: '/analysis/signal-aging',
            component: () => import('#/views/analysis/signal-aging.vue'),
            meta: {
              icon: 'lucide:battery-low',
              title: '信号老化',
            },
          },
        ],
      },
      // ── 用电分析 ──
      {
        name: 'AnalysisConsumption',
        path: '/analysis/consumption',
        meta: {
          icon: 'lucide:zap',
          title: '用电分析',
        },
        children: [
          {
            name: 'ConsumptionTrend',
            path: '/analysis/consumption-trend',
            component: () => import('#/views/analysis/consumption-trend.vue'),
            meta: {
              icon: 'lucide:line-chart',
              title: '负荷曲线',
            },
          },
        ],
      },
    ],
  },
];

export default routes;
