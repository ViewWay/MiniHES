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
