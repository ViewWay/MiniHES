import { requestClient } from '#/api/request';

export interface TestListParams {
  page?: number;
  page_size?: number;
  project_id?: number;
  test_type?: string;
  status?: string;
}

export interface TestTaskFormData {
  test_type: string;
  project_id: number;
  device_count?: number;
  description?: string;
}

export interface TestReportFormData {
  test_type: string;
  test_environment: string;
  test_duration_days: number;
  firmware_version: string;
  hardware_version: string;
  conclusion: 'pass' | 'fail';
  notes?: string;
}

export interface DefectFormData {
  title: string;
  description: string;
  severity: 'critical' | 'major' | 'minor';
  test_task_id: number;
  assigned_to?: number;
}

export function getTestList(params: TestListParams) {
  return requestClient.get('/tests', { params });
}

export function createTestTask(data: TestTaskFormData) {
  return requestClient.post('/tests', data);
}

export function getTestDetail(id: number) {
  return requestClient.get(`/tests/${id}`);
}

export function createTestReport(testId: number, data: TestReportFormData) {
  return requestClient.post(`/tests/${testId}/report`, data);
}

export function getTestReport(id: number) {
  return requestClient.get(`/tests/${id}/report`);
}

export function addDefect(testId: number, data: DefectFormData) {
  return requestClient.post(`/tests/${testId}/defects`, data);
}

export function updateDefect(id: number, data: Partial<DefectFormData> & { status?: string }) {
  return requestClient.put(`/defects/${id}`, data);
}

export function getDefects(params?: { test_id?: number; severity?: string; status?: string }) {
  return requestClient.get('/defects', { params });
}

export function exportTestReport(id: number) {
  return requestClient.get(`/tests/${id}/report/export`, { responseType: 'blob' });
}
