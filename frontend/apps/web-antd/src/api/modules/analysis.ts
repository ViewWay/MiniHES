import { requestClient } from '#/api/request';

export interface DailyAnalysisParams {
  meter_id: number;
  date: string;
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

export function getCompareAnalysis(params: CompareParams) {
  return requestClient.post('/analysis/compare', params);
}

export function getAnalysisReports(params?: { project_id?: number; page?: number }) {
  return requestClient.get('/analysis/reports', { params });
}

export function exportAnalysisReport(id: number) {
  return requestClient.get(`/analysis/reports/${id}/export`, { responseType: 'blob' });
}

export function exportDailyReport(params: { meter_id?: number; date?: string }) {
  return requestClient.get('/analysis/daily/export', { params, responseType: 'blob', responseReturn: 'body' });
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
