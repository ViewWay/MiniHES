import { useResponseSuccess } from '~/utils/response';

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000);

const tasks = [
  { id: 1, task_name: '三相表每日数据采集', task_category: 'collection', task_type: 'cron', schedule_config: { cron: '0 8 * * *' }, execution_content: { meter_ids: [1, 2, 7, 8], obis_codes: ['1.0.0.0.0.255', '1.0.12.7.0.255'] }, filter_config: {}, priority: 1, retry_times: 3, timeout: 60, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(20)), last_run: fmtDate(now), next_run: fmtDate(new Date(now.getTime() + 86400000)), today_executions: 4 },
  { id: 2, task_name: '单相表负荷曲线采集', task_category: 'collection', task_type: 'interval', schedule_config: { interval_minutes: 30 }, execution_content: { meter_ids: [3, 9], obis_codes: ['1.0.1.8.0.255'] }, filter_config: {}, priority: 2, retry_times: 2, timeout: 30, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(15)), last_run: fmtDate(now), next_run: fmtDate(new Date(now.getTime() + 30 * 60000)), today_executions: 8 },
  { id: 3, task_name: 'NB-IoT实时监控', task_category: 'collection', task_type: 'interval', schedule_config: { interval_minutes: 15 }, execution_content: { meter_ids: [4, 10], obis_codes: ['1.0.0.0.0.255'] }, filter_config: {}, priority: 1, retry_times: 5, timeout: 20, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(7)), last_run: fmtDate(now), next_run: fmtDate(new Date(now.getTime() + 15 * 60000)), today_executions: 16 },
  { id: 4, task_name: '数据一致性分析', task_category: 'analysis', task_type: 'cron', schedule_config: { cron: '0 2 * * *' }, execution_content: { analysis_type: 'consistency' }, filter_config: {}, priority: 3, retry_times: 1, timeout: 300, is_enabled: true, status: 'completed', created_at: fmtDate(daysAgo(10)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(new Date(now.getTime() + 86400000)), today_executions: 1 },
  { id: 5, task_name: 'PLC载波稳定性测试', task_category: 'collection', task_type: 'cron', schedule_config: { cron: '0 */2 * * *' }, execution_content: { meter_ids: [6, 11], obis_codes: ['1.0.0.0.0.255'] }, filter_config: {}, priority: 2, retry_times: 3, timeout: 45, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(5)), last_run: fmtDate(now), next_run: fmtDate(new Date(now.getTime() + 2 * 3600000)), today_executions: 6 },
  { id: 6, task_name: '每周测试报告生成', task_category: 'report', task_type: 'cron', schedule_config: { cron: '0 9 * * 1' }, execution_content: { report_type: 'weekly' }, filter_config: { project_ids: [1, 2] }, priority: 5, retry_times: 1, timeout: 600, is_enabled: false, status: 'paused', created_at: fmtDate(daysAgo(30)), last_run: fmtDate(daysAgo(3)), next_run: null, today_executions: 0 },
];

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;
  const status = query.status as string | undefined;
  const taskCategory = query.task_category as string | undefined;

  let filtered = [...tasks];
  if (status) filtered = filtered.filter((t) => t.status === status);
  if (taskCategory) filtered = filtered.filter((t) => t.task_category === taskCategory);

  const runningCount = filtered.filter((t) => t.status === 'running').length;
  const totalExecutions = filtered.reduce((sum, t) => sum + t.today_executions, 0);

  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return useResponseSuccess({
    items,
    total: filtered.length,
    running_count: runningCount,
    today_executions: totalExecutions,
  });
});
