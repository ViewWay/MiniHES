import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    test_id: id,
    test_type: 'type_approval',
    test_environment: '实验室标准环境 23±2℃',
    test_duration_days: 30,
    firmware_version: 'v2.1.0',
    hardware_version: 'HW3.0',
    conclusion: 'pass',
    notes: '各项指标满足GB/T 17215.321标准要求',
    created_at: '2025-05-15 10:00:00',
  });
});
