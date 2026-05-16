import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    task_name: '三相表每日数据采集',
    task_category: 'collection',
    task_type: 'cron',
    schedule_config: { cron: '0 8 * * *' },
    execution_content: { meter_ids: [1, 2, 7, 8], obis_codes: ['1.0.0.0.0.255'] },
    filter_config: {},
    priority: 1,
    retry_times: 3,
    timeout: 60,
    is_enabled: true,
    status: 'running',
    created_at: '2025-04-25 10:00:00',
  });
});
