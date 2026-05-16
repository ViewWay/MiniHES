import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    project_id: 1,
    test_type: 'type_approval',
    status: 'in_progress',
    device_count: 24,
    description: '三相智能电能表型式评价全性能测试',
    created_at: '2025-04-20 10:00:00',
    started_at: '2025-04-22 09:00:00',
  });
});
