import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;

  const logs = [
    { id: 1, user_id: 1, username: 'admin', operation_type: 'login', operation_desc: '用户登录系统', ip: '192.168.1.100', created_at: '2025-05-15 08:30:00' },
    { id: 2, user_id: 2, username: 'engineer', operation_type: 'create', operation_desc: '创建采集任务: 三相表每日数据采集', ip: '192.168.1.101', created_at: '2025-05-15 09:00:00' },
    { id: 3, user_id: 2, username: 'engineer', operation_type: 'update', operation_desc: '修改样机信息: SM-2024-0001', ip: '192.168.1.101', created_at: '2025-05-15 09:15:00' },
    { id: 4, user_id: 3, username: 'tester', operation_type: 'export', operation_desc: '导出告警数据', ip: '192.168.1.102', created_at: '2025-05-15 10:00:00' },
    { id: 5, user_id: 1, username: 'admin', operation_type: 'delete', operation_desc: '删除过期采集任务', ip: '192.168.1.100', created_at: '2025-05-14 16:00:00' },
    { id: 6, user_id: 2, username: 'engineer', operation_type: 'login', operation_desc: '用户登录系统', ip: '192.168.1.101', created_at: '2025-05-14 08:45:00' },
    { id: 7, user_id: 3, username: 'tester', operation_type: 'create', operation_desc: '创建测试报告', ip: '192.168.1.102', created_at: '2025-05-14 14:20:00' },
    { id: 8, user_id: 1, username: 'admin', operation_type: 'update', operation_desc: '修改系统配置', ip: '192.168.1.100', created_at: '2025-05-13 11:00:00' },
  ];

  const start = (page - 1) * pageSize;
  const items = logs.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: logs.length });
});
