import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    name: '三相智能电能表型式评价测试',
    description: '某厂商三相表全性能测试',
    test_leader: '张工程师',
    dev_leader: '王研发',
    status: 'testing',
    device_count: 24,
    online_count: 20,
    progress: 68,
    created_at: '2025-04-15 10:00:00',
  });
});
