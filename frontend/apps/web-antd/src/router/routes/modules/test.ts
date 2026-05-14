import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:clipboard-check',
      title: '测试管理',
      order: 5,
    },
    name: 'Test',
    path: '/test',
    children: [
      {
        name: 'TestList',
        path: '/test/list',
        component: () => import('#/views/test/list.vue'),
        meta: {
          icon: 'lucide:list',
          title: '测试列表',
        },
      },
      {
        name: 'TestReport',
        path: '/test/report/:id?',
        component: () => import('#/views/test/report.vue'),
        meta: {
          hideInMenu: true,
          title: '测试报告',
          activePath: '/test/list',
        },
      },
      {
        name: 'TestDefect',
        path: '/test/defect',
        component: () => import('#/views/test/defect.vue'),
        meta: {
          icon: 'lucide:bug',
          title: '缺陷管理',
        },
      },
    ],
  },
];

export default routes;
