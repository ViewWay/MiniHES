import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    status: 'healthy',
    uptime: '45天12小时30分',
    version: '1.0.0',
    services: {
      api: { status: 'running', response_time: '12ms' },
      celery_worker: { status: 'running', active_tasks: 3 },
      dlms_engine: { status: 'running', active_connections: 8 },
      scheduler: { status: 'running', next_task: '5分钟后' },
    },
    system: {
      cpu_usage: '23%',
      memory_usage: '45%',
      disk_usage: '62%',
      network: '正常',
    },
    last_check: new Date().toISOString().replace('T', ' ').slice(0, 19),
  });
});
