import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, meter_id: 12, meter_name: '维修中表#1', description: '显示模块故障，屏幕花屏', cost: 150, status: 'in_progress', created_at: '2025-05-08 10:00:00' },
      { id: 2, meter_id: 7, meter_name: '三相表#3', description: '通信模块更换', cost: 200, status: 'completed', created_at: '2025-04-15 09:00:00' },
    ],
    total: 2,
  });
});
