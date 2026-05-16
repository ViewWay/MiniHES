import { useResponseSuccess } from '~/utils/response';

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000);

const alarms = [
  { id: 1, meter_id: 7, meter_name: '三相表#3', alarm_type: 'communication', severity: 'critical', alarm_message: '设备持续离线超过30分钟', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(now) },
  { id: 2, meter_id: 12, meter_name: '维修中表#1', alarm_type: 'eeprom', severity: 'warning', alarm_message: 'EEPROM校验失败', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(now) },
  { id: 3, meter_id: 1, meter_name: '三相表#1', alarm_type: 'threshold', severity: 'warning', alarm_message: '相位A电压超过上限阈值', alarm_value: '245.8V', threshold_value: '240V', is_handled: true, handle_notes: '确认是测试工况，正常', created_at: fmtDate(daysAgo(1)) },
  { id: 4, meter_id: 3, meter_name: '单相表#1', alarm_type: 'anomaly', severity: 'info', alarm_message: '电流读数突变，疑似负荷变化', alarm_value: '15.2A', threshold_value: null, is_handled: true, handle_notes: '正常负荷切换', created_at: fmtDate(daysAgo(1)) },
  { id: 5, meter_id: 2, meter_name: '三相表#2', alarm_type: 'threshold', severity: 'critical', alarm_message: '总功率超过额定值', alarm_value: '12.5kW', threshold_value: '10kW', is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(1)) },
  { id: 6, meter_id: 4, meter_name: 'NB-IoT表#1', alarm_type: 'communication', severity: 'warning', alarm_message: 'NB-IoT信号强度低于阈值', alarm_value: '-120dBm', threshold_value: '-110dBm', is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(2)) },
  { id: 7, meter_id: 6, meter_name: 'PLC表#1', alarm_type: 'stack', severity: 'info', alarm_message: 'PLC载波通信重试次数增加', alarm_value: '5次', threshold_value: '3次', is_handled: true, handle_notes: '线路噪声导致，已恢复', created_at: fmtDate(daysAgo(2)) },
  { id: 8, meter_id: 8, meter_name: '三相表#4', alarm_type: 'anomaly', severity: 'warning', alarm_message: '电能计量数据跳变', alarm_value: '5.2kWh', threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(3)) },
  { id: 9, meter_id: 9, meter_name: '单相表#2', alarm_type: 'threshold', severity: 'info', alarm_message: '当前需量接近上限', alarm_value: '8.5kW', threshold_value: '10kW', is_handled: true, handle_notes: '已记录', created_at: fmtDate(daysAgo(3)) },
  { id: 10, meter_id: 10, meter_name: 'NB-IoT表#2', alarm_type: 'communication', severity: 'critical', alarm_message: '数据上报超时', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(4)) },
  { id: 11, meter_id: 1, meter_name: '三相表#1', alarm_type: 'threshold', severity: 'info', alarm_message: '频率偏差超过0.5Hz', alarm_value: '49.4Hz', threshold_value: '50±0.5Hz', is_handled: true, handle_notes: '测试工况', created_at: fmtDate(daysAgo(5)) },
  { id: 12, meter_id: 5, meter_name: '红外表#1', alarm_type: 'communication', severity: 'warning', alarm_message: '红外通信失败', alarm_value: null, threshold_value: null, is_handled: true, handle_notes: '重新对准后恢复', created_at: fmtDate(daysAgo(6)) },
];

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;
  const severity = query.severity as string | undefined;
  const alarmType = query.alarm_type as string | undefined;
  const isHandled = query.is_handled as string | undefined;

  let filtered = [...alarms];

  if (severity) {
    filtered = filtered.filter((a) => a.severity === severity);
  }
  if (alarmType) {
    filtered = filtered.filter((a) => a.alarm_type === alarmType);
  }
  if (isHandled !== undefined && isHandled !== null && isHandled !== '') {
    const handled = isHandled === 'true';
    filtered = filtered.filter((a) => a.is_handled === handled);
  }

  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: filtered.length });
});
