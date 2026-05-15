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
      {
        name: 'DbMonitor',
        path: '/system/db-monitor',
        component: () => import('#/views/system/db-monitor.vue'),
        meta: {
          icon: 'lucide:database',
          title: '数据库监控',
        },
      },
      {
        name: 'SystemHealth',
        path: '/system/health',
        component: () => import('#/views/system/health.vue'),
        meta: {
          icon: 'lucide:heart-pulse',
          title: '系统健康',
        },
      },
      {
        name: 'DataArchive',
        path: '/system/data-archive',
        component: () => import('#/views/system/data-archive.vue'),
        meta: {
          icon: 'lucide:archive',
          title: '数据归档',
        },
      },
    ],
  },
];

export default routes;
