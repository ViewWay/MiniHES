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
    ],
  },
];

export default routes;
