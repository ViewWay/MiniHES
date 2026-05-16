import { describe, expect, it, vi, beforeEach } from 'vitest';

import { requestClient } from '#/api/request';

import {
  getTaskList,
  getTaskDetail,
  createTask,
  executeTask,
  toggleTask,
  deleteTask,
  getTaskLogs,
  getTaskDeviceLog,
} from '#/api/modules/task';

vi.mock('#/api/request', () => ({
  requestClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('task API module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTaskList', () => {
    it('should call GET /tasks with pagination', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getTaskList({ page: 1, page_size: 20 });

      expect(requestClient.get).toHaveBeenCalledWith('/tasks', {
        params: { page: 1, page_size: 20 },
      });
    });

    it('should pass filter params', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getTaskList({
        page: 1,
        page_size: 20,
        status: 'running',
        task_type: 'cron',
        task_category: 'collection',
      });

      expect(requestClient.get).toHaveBeenCalledWith('/tasks', {
        params: {
          page: 1,
          page_size: 20,
          status: 'running',
          task_type: 'cron',
          task_category: 'collection',
        },
      });
    });
  });

  describe('getTaskDetail', () => {
    it('should call GET /tasks/:id', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ id: 1, task_name: 'Test' });

      const result = await getTaskDetail(1);

      expect(requestClient.get).toHaveBeenCalledWith('/tasks/1');
      expect(result.task_name).toBe('Test');
    });
  });

  describe('createTask', () => {
    it('should call POST /tasks with form data', async () => {
      const formData = {
        task_name: 'Daily Collection',
        task_category: 'collection' as const,
        task_type: 'cron' as const,
        schedule_config: { cron: '0 8 * * *' },
        execution_content: { read_obis: ['1.0.0.0.0.255'] },
        filter_config: {},
      };
      vi.mocked(requestClient.post).mockResolvedValue({ id: 1, ...formData });

      await createTask(formData);

      expect(requestClient.post).toHaveBeenCalledWith('/tasks', formData);
    });
  });

  describe('executeTask', () => {
    it('should call POST /tasks/:id/execute', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({});

      await executeTask(5, { device_ids: [1, 2, 3] });

      expect(requestClient.post).toHaveBeenCalledWith('/tasks/5/execute', {
        device_ids: [1, 2, 3],
      });
    });

    it('should work without device_ids', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({});

      await executeTask(5);

      expect(requestClient.post).toHaveBeenCalledWith('/tasks/5/execute', {});
    });
  });

  describe('toggleTask', () => {
    it('should call PATCH /tasks/:id/toggle', async () => {
      vi.mocked(requestClient.patch).mockResolvedValue({});

      await toggleTask(1, true);

      expect(requestClient.patch).toHaveBeenCalledWith('/tasks/1/toggle', {
        is_enabled: true,
      });
    });

    it('should send false when disabling', async () => {
      vi.mocked(requestClient.patch).mockResolvedValue({});

      await toggleTask(1, false);

      expect(requestClient.patch).toHaveBeenCalledWith('/tasks/1/toggle', {
        is_enabled: false,
      });
    });
  });

  describe('deleteTask', () => {
    it('should call DELETE /tasks/:id', async () => {
      vi.mocked(requestClient.delete).mockResolvedValue({});

      await deleteTask(3);

      expect(requestClient.delete).toHaveBeenCalledWith('/tasks/3');
    });
  });

  describe('getTaskLogs', () => {
    it('should call GET /tasks/:id/logs with pagination', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getTaskLogs({ task_id: 10, page: 1, page_size: 20 });

      expect(requestClient.get).toHaveBeenCalledWith('/tasks/10/logs', {
        params: { page: 1, page_size: 20 },
      });
    });
  });

  describe('getTaskDeviceLog', () => {
    it('should call GET /task-logs/:id/devices', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [] });

      await getTaskDeviceLog(42);

      expect(requestClient.get).toHaveBeenCalledWith('/task-logs/42/devices', {
        params: undefined,
      });
    });

    it('should pass status filter', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [] });

      await getTaskDeviceLog(42, { status: 'failed' });

      expect(requestClient.get).toHaveBeenCalledWith('/task-logs/42/devices', {
        params: { status: 'failed' },
      });
    });
  });
});
