import { describe, expect, it } from 'vitest';

import {
  METER_STATUS_MAP,
  METER_TYPE_MAP,
  PROTOCOL_OPTIONS,
  COMMUNICATION_TYPE_MAP,
  STATUS_FLOW_OPTIONS,
} from '#/constants/meter';

describe('meter constants', () => {
  describe('METER_STATUS_MAP', () => {
    it('should have required status entries', () => {
      const requiredStatuses = [
        'in_stock',
        'testing',
        'field_deployed',
        'borrowed',
        'maintenance',
        'scrapped',
      ];
      for (const status of requiredStatuses) {
        expect(METER_STATUS_MAP[status]).toBeDefined();
        expect(METER_STATUS_MAP[status].label).toBeTruthy();
        expect(METER_STATUS_MAP[status].color).toBeTruthy();
      }
    });

    it('should have unique labels for all statuses', () => {
      const labels = Object.values(METER_STATUS_MAP).map((s) => s.label);
      expect(new Set(labels).size).toBe(labels.length);
    });

    it('should have valid Ant Design color values', () => {
      const validColors = [
        'default',
        'blue',
        'green',
        'orange',
        'cyan',
        'red',
        'purple',
        'success',
        'error',
        'processing',
        'warning',
      ];
      for (const [, value] of Object.entries(METER_STATUS_MAP)) {
        expect(validColors).toContain(value.color);
      }
    });
  });

  describe('PROTOCOL_OPTIONS', () => {
    it('should have value and label for each option', () => {
      for (const opt of PROTOCOL_OPTIONS) {
        expect(opt.value).toBeTruthy();
        expect(opt.label).toBeTruthy();
      }
    });

    it('should include DLMS/COSEM protocol', () => {
      expect(PROTOCOL_OPTIONS.some((o) => o.value === 'dlms_cosem')).toBe(true);
    });
  });

  describe('STATUS_FLOW_OPTIONS', () => {
    it('should have valid from/to status keys', () => {
      const allStatuses = Object.keys(METER_STATUS_MAP);
      for (const flow of STATUS_FLOW_OPTIONS) {
        expect(allStatuses).toContain(flow.from);
        expect(allStatuses).toContain(flow.to);
      }
    });

    it('should not have self-transitions', () => {
      for (const flow of STATUS_FLOW_OPTIONS) {
        expect(flow.from).not.toBe(flow.to);
      }
    });

    it('should have unique from/to pairs', () => {
      const pairs = STATUS_FLOW_OPTIONS.map(
        (f) => `${f.from}->${f.to}`,
      );
      expect(new Set(pairs).size).toBe(pairs.length);
    });
  });

  describe('COMMUNICATION_TYPE_MAP', () => {
    it('should cover all major communication types', () => {
      const expectedTypes = [
        'infrared',
        'cellular_4g',
        'nb_iot',
        'm_bus',
        'lora',
        'g3_plc',
      ];
      for (const type of expectedTypes) {
        expect(COMMUNICATION_TYPE_MAP[type]).toBeDefined();
      }
    });
  });
});
