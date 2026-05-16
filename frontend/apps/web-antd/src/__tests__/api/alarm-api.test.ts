import { describe, expect, it, vi, beforeEach } from 'vitest';

import { requestClient } from '#/api/request';

import {
  getAlarmList,
  getAlarmStats,
  handleAlarm,
  exportAlarms,
  getAlarmRules,
  createAlarmRule,
  deleteAlarmRule,
} from '#/api/modules/alarm';

vi.mock('#/api/request', () => ({
  requestClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('alarm API module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAlarmList', () => {
    it('should call GET /alarms with filter params', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getAlarmList({
        page: 1,
        page_size: 20,
        severity: 'critical',
        is_handled: false,
      });

      expect(requestClient.get).toHaveBeenCalledWith('/alarms', {
        params: {
          page: 1,
          page_size: 20,
          severity: 'critical',
          is_handled: false,
        },
      });
    });
  });

  describe('getAlarmStats', () => {
    it('should call GET /alarms/stats', async () => {
      const mockStats = {
        total_count: 100,
        unhandled_count: 30,
        critical_count: 5,
      };
      vi.mocked(requestClient.get).mockResolvedValue(mockStats);

      const result = await getAlarmStats();

      expect(requestClient.get).toHaveBeenCalledWith('/alarms/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('handleAlarm', () => {
    it('should call POST /alarms/:id/handle with notes', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({});

      await handleAlarm(1, { handle_notes: '已确认处理' });

      expect(requestClient.post).toHaveBeenCalledWith('/alarms/1/handle', {
        handle_notes: '已确认处理',
      });
    });
  });

  describe('exportAlarms', () => {
    it('should call GET /alarms/export with blob response', async () => {
      vi.mocked(requestClient.get).mockResolvedValue(new Blob());

      await exportAlarms({ severity: 'critical' });

      expect(requestClient.get).toHaveBeenCalledWith('/alarms/export', {
        params: { severity: 'critical' },
        responseType: 'blob',
        responseReturn: 'body',
      });
    });
  });

  describe('alarm rule CRUD', () => {
    it('should create alarm rule', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({ id: 1 });

      await createAlarmRule({
        name: '电压过高',
        rule_type: 'threshold',
        obis_code: '1.0.12.7.0.255',
      });

      expect(requestClient.post).toHaveBeenCalledWith('/alarm-rules', {
        name: '电压过高',
        rule_type: 'threshold',
        obis_code: '1.0.12.7.0.255',
      });
    });

    it('should delete alarm rule', async () => {
      vi.mocked(requestClient.delete).mockResolvedValue({});

      await deleteAlarmRule(5);

      expect(requestClient.delete).toHaveBeenCalledWith('/alarm-rules/5');
    });

    it('should list alarm rules with pagination', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getAlarmRules({ page: 2, page_size: 10 });

      expect(requestClient.get).toHaveBeenCalledWith('/alarm-rules', {
        params: { page: 2, page_size: 10 },
      });
    });
  });
});
