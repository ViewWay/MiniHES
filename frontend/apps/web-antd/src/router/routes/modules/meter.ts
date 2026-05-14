import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:cpu',
      title: '设备管理',
      order: 1,
    },
    name: 'Meter',
    path: '/meter',
    children: [
      {
        name: 'MeterList',
        path: '/meter/list',
        component: () => import('#/views/meter/list.vue'),
        meta: {
          icon: 'lucide:list',
          title: '设备列表',
        },
      },
      {
        name: 'MeterDetail',
        path: '/meter/detail/:id',
        component: () => import('#/views/meter/detail.vue'),
        meta: {
          hideInMenu: true,
          title: '设备详情',
          activePath: '/meter/list',
        },
      },
      {
        name: 'MeterBorrow',
        path: '/meter/borrow',
        component: () => import('#/views/meter/borrow.vue'),
        meta: {
          icon: 'lucide:hand-grab',
          title: '借用管理',
        },
      },
      {
        name: 'MeterRepair',
        path: '/meter/repair',
        component: () => import('#/views/meter/repair.vue'),
        meta: {
          icon: 'lucide:wrench',
          title: '维修记录',
        },
      },
    ],
  },
];

export default routes;
