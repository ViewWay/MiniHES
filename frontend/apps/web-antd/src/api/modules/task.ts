import { requestClient } from '#/api/request';

export interface TaskListParams {
  page?: number;
  page_size?: number;
  status?: string;
  task_type?: string;
  task_category?: string;
}

export interface TaskFormData {
  task_name: string;
  task_category: 'collection' | 'analysis' | 'report' | 'cleanup';
  task_type: 'cron' | 'interval' | 'once';
  schedule_config: Record<string, any>;
  execution_content: Record<string, any>;
  filter_config: Record<string, any>;
  priority?: number;
  retry_times?: number;
  timeout?: number;
  is_enabled?: boolean;
}

export function getTaskList(params: TaskListParams) {
  return requestClient.get('/tasks', { params });
}

export function getTaskDetail(id: number) {
  return requestClient.get(`/tasks/${id}`);
}

export function createTask(data: TaskFormData) {
  return requestClient.post('/tasks', data);
}

export function updateTask(id: number, data: Partial<TaskFormData>) {
  return requestClient.put(`/tasks/${id}`, data);
}

export function deleteTask(id: number) {
  return requestClient.delete(`/tasks/${id}`);
}

export function executeTask(id: number, data?: { device_ids?: number[] }) {
  return requestClient.post(`/tasks/${id}/execute`, data || {});
}

export function toggleTask(id: number, enabled: boolean) {
  return requestClient.request(`/tasks/${id}/toggle`, { data: { is_enabled: enabled }, method: 'PATCH' });
}

export function getTaskLogs(params: { task_id: number; page?: number; page_size?: number }) {
  return requestClient.get(`/tasks/${params.task_id}/logs`, {
    params: { page: params.page, page_size: params.page_size },
  });
}

export function getTaskDeviceLog(logId: number, params?: { status?: string }) {
  return requestClient.get(`/task-logs/${logId}/devices`, { params });
}
