import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:settings',
      title: '系统管理',
      order: 10,
    },
    name: 'System',
    path: '/system',
    children: [
      {
        name: 'SystemUser',
        path: '/system/user',
        component: () => import('#/views/system/user.vue'),
        meta: {
          icon: 'lucide:users',
          title: '用户管理',
        },
      },
      {
        name: 'SystemRole',
        path: '/system/role',
        component: () => import('#/views/system/role.vue'),
        meta: {
          icon: 'lucide:shield',
          title: '角色管理',
        },
      },
      {
        name: 'SystemLog',
        path: '/system/log',
        component: () => import('#/views/system/log.vue'),
        meta: {
          icon: 'lucide:scroll-text',
          title: '操作日志',
        },
      },
      {
        name: 'ProjectManage',
        path: '/system/project',
        component: () => import('#/views/system/project.vue'),
        meta: {
          icon: 'lucide:folder-kanban',
          title: '项目管理',
        },
      },
      {
        name: 'MeterPoint',
        path: '/system/meter-point',
        component: () => import('#/views/system/meter-point.vue'),
        meta: {
          icon: 'lucide:cpu',
          title: '采集点配置',
        },
      },
      {
        name: 'AlarmRule',
        path: '/system/alarm-rule',
        component: () => import('#/views/system/alarm-rule.vue'),
        meta: {
          icon: 'lucide:bell-ring',
          title: '告警规则',
        },
      },
    ],
  },
];

export default routes;
