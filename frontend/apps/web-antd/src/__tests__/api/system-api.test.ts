import { describe, expect, it, vi, beforeEach } from 'vitest';

import { requestClient } from '#/api/request';

import {
  getUserList,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  getRoleList,
  createRole,
  getAuditLogs,
  getSystemHealth,
  getDbMonitorStats,
} from '#/api/modules/system';

vi.mock('#/api/request', () => ({
  requestClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('system API module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('user CRUD', () => {
    it('should list users with pagination', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({
        items: [],
        total: 0,
      });

      await getUserList({ page: 1, page_size: 20 });

      expect(requestClient.get).toHaveBeenCalledWith('/users', {
        params: { page: 1, page_size: 20 },
      });
    });

    it('should create user', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({ id: 1 });

      await createUser({
        username: 'admin',
        name: 'Admin',
        email: 'admin@test.com',
        role_ids: [1],
        password: 'secret',
      });

      expect(requestClient.post).toHaveBeenCalledWith('/users', {
        username: 'admin',
        name: 'Admin',
        email: 'admin@test.com',
        role_ids: [1],
        password: 'secret',
      });
    });

    it('should update user', async () => {
      vi.mocked(requestClient.put).mockResolvedValue({});

      await updateUser(1, { name: 'New Name' });

      expect(requestClient.put).toHaveBeenCalledWith('/users/1', {
        name: 'New Name',
      });
    });

    it('should delete user', async () => {
      vi.mocked(requestClient.delete).mockResolvedValue({});

      await deleteUser(5);

      expect(requestClient.delete).toHaveBeenCalledWith('/users/5');
    });

    it('should reset password without exposing default', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({});

      await resetUserPassword(1);

      expect(requestClient.post).toHaveBeenCalledWith(
        '/users/1/reset-password',
      );
    });
  });

  describe('role CRUD', () => {
    it('should list roles', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({
        items: [{ id: 1, name: 'admin' }],
      });

      const result = await getRoleList();

      expect(requestClient.get).toHaveBeenCalledWith('/roles', {
        params: undefined,
      });
      expect(result.items).toHaveLength(1);
    });

    it('should create role with permissions', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({ id: 1 });

      await createRole({
        name: 'operator',
        code: 'OP',
        description: 'Operator role',
        permission_ids: [1, 2, 3],
      });

      expect(requestClient.post).toHaveBeenCalledWith('/roles', {
        name: 'operator',
        code: 'OP',
        description: 'Operator role',
        permission_ids: [1, 2, 3],
      });
    });
  });

  describe('audit logs', () => {
    it('should fetch logs with filters', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getAuditLogs({
        page: 1,
        page_size: 20,
        operation_type: 'CREATE',
        resource_type: 'meter',
      });

      expect(requestClient.get).toHaveBeenCalledWith('/audit-logs', {
        params: {
          page: 1,
          page_size: 20,
          operation_type: 'CREATE',
          resource_type: 'meter',
        },
      });
    });
  });

  describe('system monitoring', () => {
    it('should get health status', async () => {
      const mockHealth = {
        status: 'healthy',
        services: [
          { name: 'API', status: 'up' },
          { name: 'DB', status: 'up' },
        ],
      };
      vi.mocked(requestClient.get).mockResolvedValue(mockHealth);

      const result = await getSystemHealth();

      expect(requestClient.get).toHaveBeenCalledWith('/system/health');
      expect(result.status).toBe('healthy');
    });

    it('should get DB monitor stats', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ postgres: {}, redis: {} });

      const result = await getDbMonitorStats();

      expect(requestClient.get).toHaveBeenCalledWith('/system/db-monitor');
      expect(result.postgres).toBeDefined();
      expect(result.redis).toBeDefined();
    });
  });
});
