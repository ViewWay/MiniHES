import { requestClient } from '#/api/request';

export interface MeterListParams {
  page?: number;
  page_size?: number;
  project_id?: number;
  status?: string;
  keyword?: string;
}

export interface MeterFormData {
  serial_number: string;
  meter_name: string;
  meter_type_id: number;
  project_id: number;
  protocol: string;
  line_type: string;
  manufacturer?: string;
  model?: string;
  firmware_version?: string;
  hardware_version?: string;
  frame_number?: string;
  location?: string;
  factory_date?: string;
  purchase_date?: string;
  warranty_date?: string;
  notes?: string;
}

export interface BorrowFormData {
  meter_id: number;
  borrower_name: string;
  expected_return_date: string;
  borrow_reason: string;
  department_approver?: number;
}

export interface RepairFormData {
  meter_id: number;
  description: string;
  cost?: number;
}

export function getMeterList(params: MeterListParams) {
  return requestClient.get('/meters', { params });
}

export function getMeterDetail(id: number) {
  return requestClient.get(`/meters/${id}`);
}

export function createMeter(data: MeterFormData) {
  return requestClient.post('/meters', data);
}

export function updateMeter(id: number, data: Partial<MeterFormData>) {
  return requestClient.put(`/meters/${id}`, data);
}

export function changeMeterStatus(id: number, data: { status: string; reason: string }) {
  return requestClient.post(`/meters/${id}/status`, data);
}

export function borrowMeter(id: number, data: BorrowFormData) {
  return requestClient.post(`/meters/${id}/borrow`, data);
}

export function createBorrowRequest(data: BorrowFormData) {
  return requestClient.post('/meters/borrows', data);
}

export function getBorrowRecords(params?: { meter_id?: number; status?: string }) {
  return requestClient.get('/meters/borrows', { params });
}

export function approveBorrow(id: number, data: { approved: boolean; comment?: string }) {
  return requestClient.post(`/borrows/${id}/approve`, data);
}

export function returnBorrow(id: number) {
  return requestClient.post(`/borrows/${id}/return`);
}

export function getRepairRecords(params?: { meter_id?: number; status?: string; start_date?: string; end_date?: string }) {
  return requestClient.get('/meters/repairs', { params });
}

export function addRepairRecord(data: RepairFormData) {
  return requestClient.post('/meters/repairs', data);
}

export function getMeterStatusHistory(id: number) {
  return requestClient.get(`/meters/${id}/status-history`);
}

export function getMeterAttachments(id: number) {
  return requestClient.get(`/meters/${id}/attachments`);
}

export function uploadMeterAttachment(id: number, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post(`/meters/${id}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function importMeters(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post('/meters/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function exportMeters(params?: MeterListParams) {
  return requestClient.get('/meters/export', { params, responseType: 'blob' });
}
