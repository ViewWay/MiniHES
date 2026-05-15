import { requestClient } from '#/api/request';

export interface Project {
  id: number;
  name: string;
  description?: string;
  test_leader?: string;
  dev_leader?: string;
  status?: string;
  created_at?: string;
}

export interface MeterType {
  id: number;
  name: string;
  code: string;
  description?: string;
}

export interface WireType {
  id: number;
  name: string;
  code: string;
}

export function getProjectList(params?: { page?: number; keyword?: string }) {
  return requestClient.get('/projects', { params });
}

export function getProjectDetail(id: number) {
  return requestClient.get(`/projects/${id}`);
}

export function createProject(data: Partial<Project>) {
  return requestClient.post('/projects', data);
}

export function getMeterTypes() {
  return requestClient.get('/meter-types');
}

export function getWireTypes() {
  return requestClient.get('/wire-types');
}

export function updateProject(id: number, data: Partial<Project>) {
  return requestClient.put(`/projects/${id}`, data);
}

export function deleteProject(id: number) {
  return requestClient.delete(`/projects/${id}`);
}

export function getMeterPoints(params?: { protocol?: string }) {
  return requestClient.get('/meter-points', { params });
}

export function createMeterPoint(data: any) {
  return requestClient.post('/meter-points', data);
}

export function updateMeterPoint(id: number, data: any) {
  return requestClient.put(`/meter-points/${id}`, data);
}

export function deleteMeterPoint(id: number) {
  return requestClient.delete(`/meter-points/${id}`);
}
