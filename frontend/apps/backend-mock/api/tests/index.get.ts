import { useResponseSuccess } from '~/utils/response';

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000);

const tests = [
  { id: 1, project_id: 1, test_type: 'type_approval', status: 'in_progress', device_count: 24, description: '三相智能电能表型式评价全性能测试', created_at: fmtDate(daysAgo(25)), started_at: fmtDate(daysAgo(23)) },
  { id: 2, project_id: 2, test_type: 'protocol_conformance', status: 'in_progress', device_count: 12, description: 'DLMS/COSEM协议一致性验证', created_at: fmtDate(daysAgo(12)), started_at: fmtDate(daysAgo(10)) },
  { id: 3, project_id: 3, test_type: 'stability', status: 'in_progress', device_count: 8, description: 'NB-IoT通信长期稳定性测试', created_at: fmtDate(daysAgo(5)), started_at: fmtDate(daysAgo(5)) },
  { id: 4, project_id: 4, test_type: 'functional', status: 'completed', device_count: 6, description: '红外抄表功能验证', created_at: fmtDate(daysAgo(40)), started_at: fmtDate(daysAgo(38)) },
  { id: 5, project_id: 5, test_type: 'performance', status: 'pending', device_count: 16, description: 'G3-PLC载波通信性能测试', created_at: fmtDate(daysAgo(3)), started_at: null },
];

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;
  const projectId = query.project_id as string | undefined;
  const testType = query.test_type as string | undefined;
  const status = query.status as string | undefined;

  let filtered = [...tests];
  if (projectId) filtered = filtered.filter((t) => t.project_id === Number(projectId));
  if (testType) filtered = filtered.filter((t) => t.test_type === testType);
  if (status) filtered = filtered.filter((t) => t.status === status);

  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: filtered.length });
});
