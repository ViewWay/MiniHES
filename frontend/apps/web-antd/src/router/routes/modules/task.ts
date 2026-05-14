import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:clock',
      title: '采集任务',
      order: 2,
    },
    name: 'Task',
    path: '/task',
    children: [
      {
        name: 'TaskList',
        path: '/task/list',
        component: () => import('#/views/task/list.vue'),
        meta: {
          icon: 'lucide:list-checks',
          title: '任务列表',
        },
      },
      {
        name: 'TaskCreate',
        path: '/task/create',
        component: () => import('#/views/task/create.vue'),
        meta: {
          icon: 'lucide:plus-circle',
          title: '创建任务',
        },
      },
      {
        name: 'TaskLogs',
        path: '/task/logs',
        component: () => import('#/views/task/logs.vue'),
        meta: {
          icon: 'lucide:file-text',
          title: '执行日志',
        },
      },
      {
        name: 'TaskMonitor',
        path: '/task/monitor',
        component: () => import('#/views/task/monitor.vue'),
        meta: {
          icon: 'lucide:monitor',
          title: '任务监控',
        },
      },
    ],
  },
];

export default routes;
