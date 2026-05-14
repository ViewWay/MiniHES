import { requestClient } from '#/api/request';

export interface AlarmListParams {
  page?: number;
  page_size?: number;
  severity?: string;
  alarm_type?: string;
  is_handled?: boolean;
  start_date?: string;
  end_date?: string;
}

export interface AlarmHandleData {
  handle_notes: string;
}

export function getAlarmList(params?: AlarmListParams) {
  return requestClient.get('/alarms', { params });
}

export function getAlarmDetail(id: number) {
  return requestClient.get(`/alarms/${id}`);
}

export function handleAlarm(id: number, data: AlarmHandleData) {
  return requestClient.post(`/alarms/${id}/handle`, data);
}

export function getAlarmStats() {
  return requestClient.get('/alarms/stats');
}

export function exportAlarms(params?: AlarmListParams) {
  return requestClient.get('/alarms/export', { params, responseType: 'blob', responseReturn: 'body' });
}

// Alarm Rule APIs
export function getAlarmRules(params?: { page?: number; page_size?: number; rule_type?: string }) {
  return requestClient.get('/alarm-rules', { params });
}

export function createAlarmRule(data: any) {
  return requestClient.post('/alarm-rules', data);
}

export function updateAlarmRule(id: number, data: any) {
  return requestClient.put(`/alarm-rules/${id}`, data);
}

export function deleteAlarmRule(id: number) {
  return requestClient.delete(`/alarm-rules/${id}`);
}
