import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;

  const users = [
    { id: 1, username: 'admin', name: '超级管理员', email: 'admin@minihes.com', phone: '13800000001', role_ids: [1], roles: ['super'], status: 'active', created_at: '2025-01-01 00:00:00' },
    { id: 2, username: 'engineer', name: '张工程师', email: 'zhang@minihes.com', phone: '13800000002', role_ids: [2], roles: ['admin'], status: 'active', created_at: '2025-01-15 10:00:00' },
    { id: 3, username: 'tester', name: '李测试员', email: 'li@minihes.com', phone: '13800000003', role_ids: [3], roles: ['user'], status: 'active', created_at: '2025-02-01 09:00:00' },
    { id: 4, username: 'wang', name: '王研发', email: 'wang@minihes.com', phone: '13800000004', role_ids: [2], roles: ['admin'], status: 'active', created_at: '2025-02-10 10:00:00' },
    { id: 5, username: 'liu', name: '刘硬件', email: 'liu@minihes.com', phone: '13800000005', role_ids: [3], roles: ['user'], status: 'inactive', created_at: '2025-03-01 11:00:00' },
  ];

  const start = (page - 1) * pageSize;
  const items = users.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: users.length });
});
