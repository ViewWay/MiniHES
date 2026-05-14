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

export function getMeterPoints(params?: { protocol?: string }) {
  return requestClient.get('/meter-points', { params });
}
