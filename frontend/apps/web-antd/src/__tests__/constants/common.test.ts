import { describe, expect, it } from 'vitest';

import { DEFAULT_PAGE_SIZE, METADATA_FETCH_SIZE, POLL_INTERVALS, THEME_COLORS } from '#/constants/common';

describe('common constants', () => {
  describe('DEFAULT_PAGE_SIZE', () => {
    it('should be a positive integer', () => {
      expect(DEFAULT_PAGE_SIZE).toBeGreaterThan(0);
      expect(Number.isInteger(DEFAULT_PAGE_SIZE)).toBe(true);
    });
  });

  describe('METADATA_FETCH_SIZE', () => {
    it('should be larger than DEFAULT_PAGE_SIZE', () => {
      expect(METADATA_FETCH_SIZE).toBeGreaterThan(DEFAULT_PAGE_SIZE);
    });
  });

  describe('POLL_INTERVALS', () => {
    it('should have all required intervals', () => {
      expect(POLL_INTERVALS.ALARM).toBeDefined();
      expect(POLL_INTERVALS.TASK_MONITOR).toBeDefined();
      expect(POLL_INTERVALS.TASK_LOGS).toBeDefined();
      expect(POLL_INTERVALS.HEALTH).toBeDefined();
      expect(POLL_INTERVALS.DB_MONITOR).toBeDefined();
      expect(POLL_INTERVALS.METER_REALTIME).toBeDefined();
    });

    it('should have reasonable interval values (>= 1s)', () => {
      for (const [, value] of Object.entries(POLL_INTERVALS)) {
        expect(value).toBeGreaterThanOrEqual(1000);
      }
    });

    it('realtime polling should be faster than batch polling', () => {
      expect(POLL_INTERVALS.METER_REALTIME).toBeLessThan(
        POLL_INTERVALS.ALARM,
      );
    });
  });

  describe('THEME_COLORS', () => {
    it('should have all required color tokens', () => {
      const requiredColors = [
        'SUCCESS',
        'WARNING',
        'ERROR',
        'PROCESSING',
        'ORANGE',
        'PURPLE',
        'TEXT_SECONDARY',
        'TEXT_TERTIARY',
      ];
      for (const color of requiredColors) {
        expect(THEME_COLORS[color as keyof typeof THEME_COLORS]).toBeDefined();
      }
    });

    it('should be valid hex colors', () => {
      const hexPattern = /^#[0-9a-fA-F]{6}$/;
      for (const [, value] of Object.entries(THEME_COLORS)) {
        expect(value).toMatch(hexPattern);
      }
    });
  });
});
