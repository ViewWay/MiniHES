import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess([
    { status: 'in_stock', reason: '样机入库', created_at: '2024-04-01 10:00:00' },
    { status: 'in_use', reason: '挂表测试', created_at: '2024-04-15 09:00:00' },
  ]);
});
