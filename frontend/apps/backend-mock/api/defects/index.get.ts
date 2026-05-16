import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, title: '电压采样偏差偏大', description: 'A相电压采样偏差超过0.5%', severity: 'major', test_task_id: 1, status: 'open', assigned_to: 2, created_at: '2025-05-10 14:00:00' },
      { id: 2, title: '红外通信偶发超时', description: '红外通信在强光下偶发超时', severity: 'minor', test_task_id: 4, status: 'resolved', assigned_to: 1, created_at: '2025-04-20 10:00:00' },
    ],
    total: 2,
  });
});
