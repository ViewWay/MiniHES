import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { meter_id: 1, meter_name: '三相表#1', avg_voltage: 220.3, max_voltage: 225.1, min_voltage: 216.8, avg_current: 6.2, max_current: 12.5, total_energy: 148.5, data_quality_score: 98.5 },
      { meter_id: 2, meter_name: '三相表#2', avg_voltage: 219.8, max_voltage: 224.3, min_voltage: 217.1, avg_current: 5.8, max_current: 11.9, total_energy: 135.2, data_quality_score: 97.1 },
      { meter_id: 3, meter_name: '单相表#1', avg_voltage: 221.1, max_voltage: 223.8, min_voltage: 218.9, avg_current: 3.5, max_current: 8.2, total_energy: 82.6, data_quality_score: 99.2 },
    ],
  });
});
