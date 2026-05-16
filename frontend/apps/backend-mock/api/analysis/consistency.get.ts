import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { meter_id: 1, meter_name: '三相表#1', check_type: 'energy_balance', result: 'pass', score: 100, details: '正反向电能平衡', checked_at: '2025-05-15 02:00:00' },
      { meter_id: 2, meter_name: '三相表#2', check_type: 'energy_balance', result: 'pass', score: 99.8, details: '微小偏差在允许范围内', checked_at: '2025-05-15 02:00:00' },
      { meter_id: 7, meter_name: '三相表#3', check_type: 'energy_balance', result: 'fail', score: 85.3, details: '正向有功电能与分相之和偏差超过1%', checked_at: '2025-05-15 02:00:00' },
      { meter_id: 1, meter_name: '三相表#1', check_type: 'load_profile', result: 'pass', score: 98.5, details: '负荷曲线完整性良好', checked_at: '2025-05-15 02:00:00' },
      { meter_id: 3, meter_name: '单相表#1', check_type: 'load_profile', result: 'warning', score: 92.1, details: '存在少量数据缺失', checked_at: '2025-05-15 02:00:00' },
    ],
    summary: { total: 5, pass: 3, warning: 1, fail: 1 },
    last_check: '2025-05-15 02:00:00',
  });
});
