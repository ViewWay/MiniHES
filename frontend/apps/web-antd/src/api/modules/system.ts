import { requestClient } from '#/api/request';

export interface UserListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  role?: string;
}

export interface UserFormData {
  username: string;
  name: string;
  email: string;
  phone?: string;
  role_ids: number[];
  password?: string;
}

export interface RoleFormData {
  name: string;
  code: string;
  description?: string;
  permission_ids: number[];
}

export function getUserList(params: UserListParams) {
  return requestClient.get('/system/users', { params });
}

export function createUser(data: UserFormData) {
  return requestClient.post('/system/users', data);
}

export function updateUser(id: number, data: Partial<UserFormData>) {
  return requestClient.put(`/system/users/${id}`, data);
}

export function deleteUser(id: number) {
  return requestClient.delete(`/system/users/${id}`);
}

export function resetUserPassword(id: number) {
  return requestClient.post(`/system/users/${id}/reset-password`);
}

export function getRoleList(params?: { page?: number }) {
  return requestClient.get('/system/roles', { params });
}

export function createRole(data: RoleFormData) {
  return requestClient.post('/system/roles', data);
}

export function updateRole(id: number, data: Partial<RoleFormData>) {
  return requestClient.put(`/system/roles/${id}`, data);
}

export function deleteRole(id: number) {
  return requestClient.delete(`/system/roles/${id}`);
}

export function getPermissionTree() {
  return requestClient.get('/system/permissions/tree');
}

export function getAuditLogs(params?: {
  user_id?: number;
  operation_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}) {
  return requestClient.get('/system/audit-logs', { params });
}

export function exportAuditLogs(params?: any) {
  return requestClient.get('/system/audit-logs/export', { params, responseType: 'blob', responseReturn: 'body' });
}

export interface ArchiveRecordParams {
  page?: number;
  page_size?: number;
}

export interface ArchiveFormData {
  archive_type: string;
  table_name: string;
  days_to_archive: number;
}

export function getArchiveRecords(params?: ArchiveRecordParams) {
  return requestClient.get('/system/data-archive', { params });
}

export function createArchive(data: ArchiveFormData) {
  return requestClient.post('/system/data-archive', data);
}

export function getDbMonitorStats() {
  return requestClient.get('/system/db-monitor');
}

export function getSystemHealth() {
  return requestClient.get('/system/health');
}
