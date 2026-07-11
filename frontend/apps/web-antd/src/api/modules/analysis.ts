import { requestClient } from '#/api/request';

export interface DailyAnalysisParams {
  meter_id: number;
  date_from: string;
  date_to: string;
}

export interface DailyMetersParams {
  project_id?: number;
}

export interface CompareParams {
  meter_ids: number[];
  start_date: string;
  end_date: string;
  point_codes?: string[];
}

export function getDailyAnalysis(params: DailyAnalysisParams) {
  return requestClient.get('/analysis/daily', { params });
}

export function getDailyMeters(params?: DailyMetersParams) {
  return requestClient.get('/analysis/daily/meters', { params });
}

export function exportDailyReport(params: DailyAnalysisParams) {
  return requestClient.get('/analysis/daily/export', {
    params,
    responseType: 'blob',
    responseReturn: 'body',
  });
}

export function getCompareAnalysis(params: CompareParams) {
  return requestClient.post('/analysis/compare', params);
}

export function getAnalysisReports(params?: { project_id?: number; page?: number }) {
  return requestClient.get('/analysis/reports', { params });
}

export function exportAnalysisReport(id: number) {
  return requestClient.get(`/analysis/reports/${id}/export`, { responseType: 'blob', responseReturn: 'body' });
}

export function getConsistencyCheck(params?: { project_id?: number }) {
  return requestClient.get('/analysis/consistency', { params });
}

export function triggerConsistencyCheck() {
  return requestClient.post('/analysis/consistency/check');
}

export interface DataQualityParams {
  page?: number;
  page_size?: number;
  meter_id?: number;
  start_date?: string;
  end_date?: string;
  min_score?: number;
  project_id?: number;
}

export function getDataQuality(params?: DataQualityParams) {
  return requestClient.get('/analysis/data-quality', { params });
}

export function exportDataQuality(params?: DataQualityParams) {
  return requestClient.get('/analysis/data-quality/export', { params, responseType: 'blob', responseReturn: 'body' });
}

// ══════════════════════════════════════════════════════════════════════
// 运维报表 API (Operation Reports)
// ══════════════════════════════════════════════════════════════════════

export interface ReportParams {
  date_from?: string;
  date_to?: string;
  project_id?: number;
  page?: number;
  page_size?: number;
}

// R-01 通信成功率
export function getCommSuccessRate(params?: ReportParams) {
  return requestClient.get('/analysis/comm-success-rate', { params });
}

// UC-8 未通信设备
export function getNonCommDevices(params?: { hours_min?: number; project_id?: number; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/non-comm-devices', { params });
}

// R-07 抄表完整率
export function getReadCompleteness(params?: ReportParams) {
  return requestClient.get('/analysis/read-completeness', { params });
}

// R-10 重试分析
export function getRetryAnalysis(params?: ReportParams) {
  return requestClient.get('/analysis/retry-analysis', { params });
}

// R-12 未确认告警报表
export function getOpenAlarmsReport(params?: { severity?: string; alarm_type?: string; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/open-alarms-report', { params });
}

// R-13 告警趋势
export function getAlarmTrend(params?: { date_from?: string; date_to?: string; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/alarm-trend', { params });
}

// R-16 设备健康
export function getDeviceHealth(params?: { project_id?: number; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/device-health', { params });
}

// R-18 信号老化
export function getSignalAging(params?: { project_id?: number; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/signal-aging', { params });
}

// R-30 负荷曲线
export function getConsumptionTrend(params?: { meter_id?: number; date_from?: string; date_to?: string; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/consumption-trend', { params });
}

// R-11 按需抄表历史
export function getOndemandHistory(params?: { date_from?: string; date_to?: string; page?: number; page_size?: number }) {
  return requestClient.get('/analysis/ondemand-history', { params });
}
