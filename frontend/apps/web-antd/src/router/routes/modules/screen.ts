import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:tv',
      title: '大屏展示',
      order: 4,
    },
    name: 'Screen',
    path: '/screen',
    children: [
      {
        name: 'ScreenOverview',
        path: '/screen/overview',
        component: () => import('#/views/screen/overview.vue'),
        meta: {
          icon: 'lucide:layout-dashboard',
          title: '项目概览大屏',
        },
      },
      {
        name: 'ScreenProject',
        path: '/screen/project',
        component: () => import('#/views/screen/project.vue'),
        meta: {
          hideInMenu: true,
          title: '项目详情大屏',
        },
      },
      {
        name: 'ScreenMeter',
        path: '/screen/meter/:id?',
        component: () => import('#/views/screen/meter.vue'),
        meta: {
          hideInMenu: true,
          title: '单表监控大屏',
        },
      },
    ],
  },
];

export default routes;
