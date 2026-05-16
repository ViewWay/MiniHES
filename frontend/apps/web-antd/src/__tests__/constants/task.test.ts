import { describe, expect, it } from 'vitest';

import {
  TASK_STATUS_MAP,
  TASK_TYPE_MAP,
  TASK_PRIORITY_MAP,
  LOG_STATUS_MAP,
} from '#/constants/task';

describe('task constants', () => {
  describe('TASK_STATUS_MAP', () => {
    it('should cover all task lifecycle states', () => {
      const requiredStatuses = [
        'pending',
        'running',
        'completed',
        'failed',
        'cancelled',
      ];
      for (const status of requiredStatuses) {
        expect(TASK_STATUS_MAP[status]).toBeDefined();
      }
    });

    it('should have label and color for each status', () => {
      for (const [, value] of Object.entries(TASK_STATUS_MAP)) {
        expect(value.label).toBeTruthy();
        expect(value.color).toBeTruthy();
      }
    });
  });

  describe('TASK_PRIORITY_MAP', () => {
    it('should have numeric string keys', () => {
      for (const key of Object.keys(TASK_PRIORITY_MAP)) {
        expect(Number(key)).not.toBeNaN();
      }
    });

    it('should include medium priority (5)', () => {
      expect(TASK_PRIORITY_MAP['5']).toBeDefined();
      expect(TASK_PRIORITY_MAP['5']!.label).toBe('中');
    });
  });

  describe('TASK_TYPE_MAP', () => {
    it('should include daily_read type', () => {
      expect(TASK_TYPE_MAP['daily_read']).toBe('日常抄表');
    });

    it('should have Chinese labels', () => {
      for (const [, label] of Object.entries(TASK_TYPE_MAP)) {
        // Chinese characters match
        expect(label).toMatch(/[一-鿿]/);
      }
    });
  });

  describe('LOG_STATUS_MAP', () => {
    it('should have success and failure statuses', () => {
      expect(LOG_STATUS_MAP.success).toBeDefined();
      expect(LOG_STATUS_MAP.failed).toBeDefined();
    });
  });
});
