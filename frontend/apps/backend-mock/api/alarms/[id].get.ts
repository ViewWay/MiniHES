import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    meter_id: 1,
    meter_name: '三相表#1',
    alarm_type: 'threshold',
    severity: 'warning',
    alarm_message: '相位A电压超过上限阈值',
    alarm_value: '245.8V',
    threshold_value: '240V',
    is_handled: true,
    handle_notes: '确认是测试工况',
    created_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
  });
});
