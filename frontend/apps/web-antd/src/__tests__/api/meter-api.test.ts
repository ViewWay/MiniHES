import { describe, expect, it, vi, beforeEach } from 'vitest';

import { requestClient } from '#/api/request';

import {
  getMeterList,
  getMeterDetail,
  createMeter,
  updateMeter,
  changeMeterStatus,
  borrowMeter,
  getBorrowRecords,
  getRepairRecords,
  addRepairRecord,
  exportMeters,
} from '#/api/modules/meter';

vi.mock('#/api/request', () => ({
  requestClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('meter API module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getMeterList', () => {
    it('should call GET /meters with params', async () => {
      const mockResponse = {
        items: [
          { id: 1, serial_number: 'SN001', meter_name: '电表1' },
        ],
        total: 1,
      };
      vi.mocked(requestClient.get).mockResolvedValue(mockResponse);

      const result = await getMeterList({ page: 1, page_size: 20 });

      expect(requestClient.get).toHaveBeenCalledWith('/meters', {
        params: { page: 1, page_size: 20 },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should pass filter params correctly', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getMeterList({
        page: 1,
        status: 'active',
        keyword: 'test',
        project_id: 5,
      });

      expect(requestClient.get).toHaveBeenCalledWith('/meters', {
        params: { page: 1, status: 'active', keyword: 'test', project_id: 5 },
      });
    });
  });

  describe('getMeterDetail', () => {
    it('should call GET /meters/:id', async () => {
      const mockMeter = { id: 42, serial_number: 'SN042' };
      vi.mocked(requestClient.get).mockResolvedValue(mockMeter);

      const result = await getMeterDetail(42);

      expect(requestClient.get).toHaveBeenCalledWith('/meters/42');
      expect(result).toEqual(mockMeter);
    });
  });

  describe('createMeter', () => {
    it('should call POST /meters with form data', async () => {
      const formData = {
        serial_number: 'SN001',
        meter_name: '新电表',
        meter_type_id: 1,
        project_id: 2,
        protocol: 'dlms_cosem',
        line_type: 'single',
      };
      vi.mocked(requestClient.post).mockResolvedValue({ id: 1, ...formData });

      await createMeter(formData);

      expect(requestClient.post).toHaveBeenCalledWith('/meters', formData);
    });
  });

  describe('updateMeter', () => {
    it('should call PUT /meters/:id with partial data', async () => {
      vi.mocked(requestClient.put).mockResolvedValue({});

      await updateMeter(1, { meter_name: '更新名称' });

      expect(requestClient.put).toHaveBeenCalledWith('/meters/1', {
        meter_name: '更新名称',
      });
    });
  });

  describe('changeMeterStatus', () => {
    it('should call POST /meters/:id/status', async () => {
      vi.mocked(requestClient.post).mockResolvedValue({});

      await changeMeterStatus(1, { status: 'testing', reason: '开始测试' });

      expect(requestClient.post).toHaveBeenCalledWith('/meters/1/status', {
        status: 'testing',
        reason: '开始测试',
      });
    });
  });

  describe('getRepairRecords', () => {
    it('should support date range and status filters', async () => {
      vi.mocked(requestClient.get).mockResolvedValue({ items: [], total: 0 });

      await getRepairRecords({
        status: 'pending',
        start_date: '2025-01-01',
        end_date: '2025-01-31',
      });

      expect(requestClient.get).toHaveBeenCalledWith('/meters/repairs', {
        params: {
          status: 'pending',
          start_date: '2025-01-01',
          end_date: '2025-01-31',
        },
      });
    });
  });
});
