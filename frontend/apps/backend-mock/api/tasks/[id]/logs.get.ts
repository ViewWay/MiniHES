import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, task_id: 1, status: 'success', started_at: '2025-05-15 08:00:00', finished_at: '2025-05-15 08:01:30', duration_ms: 90000, success_count: 3, fail_count: 1 },
      { id: 2, task_id: 1, status: 'success', started_at: '2025-05-14 08:00:00', finished_at: '2025-05-14 08:02:10', duration_ms: 130000, success_count: 4, fail_count: 0 },
    ],
    total: 2,
  });
});
