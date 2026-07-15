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
  });
}

export function getCompareAnalysis(params: CompareParams) {
  return requestClient.post('/analysis/compare', params);
}

export function getAnalysisReports(params?: {
  project_id?: number;
  page?: number;
}) {
  return requestClient.get('/analysis/reports', { params });
}

export function exportAnalysisReport(id: number) {
  return requestClient.get(`/analysis/reports/${id}/export`, {
    responseType: 'blob',
  });
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
  return requestClient.get('/analysis/data-quality/export', {
    params,
    responseType: 'blob',
  });
}

// ══════════════════════════════════════════════════════════════════════
// 电表详情看板 API
// ══════════════════════════════════════════════════════════════════════

export interface MeterDetailParams {
  meter_id?: number;
  db?: string;
  collection?: string;
  days?: number;
}

export function getAnalysisMeterDetail(params: MeterDetailParams) {
  return requestClient.get('/analysis/meter-detail', { params });
}

// ══════════════════════════════════════════════════════════════════════
// 运维报表 API
// ══════════════════════════════════════════════════════════════════════

export interface ReportParams {
  date_from?: string;
  date_to?: string;
  project_id?: number;
  page?: number;
  page_size?: number;
}

export function getCommSuccessRate(params?: ReportParams) {
  return requestClient.get('/analysis/comm-success-rate', { params });
}

export function getNonCommDevices(
  params?: {
    hours_min?: number;
    project_id?: number;
    page?: number;
    page_size?: number;
  },
) {
  return requestClient.get('/analysis/non-comm-devices', { params });
}

export function getReadCompleteness(params?: ReportParams) {
  return requestClient.get('/analysis/read-completeness', { params });
}

export function getRetryAnalysis(params?: ReportParams) {
  return requestClient.get('/analysis/retry-analysis', { params });
}

export function getOpenAlarmsReport(
  params?: {
    severity?: string;
    alarm_type?: string;
    page?: number;
    page_size?: number;
  },
) {
  return requestClient.get('/analysis/open-alarms-report', { params });
}

export function getAlarmTrend(
  params?: {
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  },
) {
  return requestClient.get('/analysis/alarm-trend', { params });
}

export function getDeviceHealth(
  params?: { project_id?: number; page?: number; page_size?: number },
) {
  return requestClient.get('/analysis/device-health', { params });
}

export function getSignalAging(
  params?: { project_id?: number; page?: number; page_size?: number },
) {
  return requestClient.get('/analysis/signal-aging', { params });
}

export function getConsumptionTrend(
  params?: {
    meter_id?: number;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  },
) {
  return requestClient.get('/analysis/consumption-trend', { params });
}

export function getOndemandHistory(
  params?: {
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  },
) {
  return requestClient.get('/analysis/ondemand-history', { params });
}
