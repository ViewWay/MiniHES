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
        name: 'AnalysisMeterDetail',
        path: '/analysis/meter-detail',
        component: () => import('#/views/analysis/meter-detail.vue'),
        meta: {
          icon: 'lucide:monitor-smartphone',
          title: '电表详情看板',
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
];

export default routes;
