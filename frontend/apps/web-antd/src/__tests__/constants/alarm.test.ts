import { describe, expect, it } from 'vitest';

import {
  ALARM_SEVERITY_MAP,
  ALARM_TYPE_MAP,
  ALARM_SEVERITY_OPTIONS,
  ALARM_TYPE_OPTIONS,
} from '#/constants/alarm';

describe('alarm constants', () => {
  describe('ALARM_SEVERITY_MAP', () => {
    it('should have critical, warning, and info levels', () => {
      expect(ALARM_SEVERITY_MAP.critical).toBeDefined();
      expect(ALARM_SEVERITY_MAP.warning).toBeDefined();
      expect(ALARM_SEVERITY_MAP.info).toBeDefined();
    });
  });

  describe('ALARM_SEVERITY_OPTIONS', () => {
    it('should be derived from ALARM_SEVERITY_MAP', () => {
      const mapKeys = Object.keys(ALARM_SEVERITY_MAP);
      const optionValues = ALARM_SEVERITY_OPTIONS.map((o) => o.value);
      expect(optionValues.sort()).toEqual(mapKeys.sort());
    });
  });

  describe('ALARM_TYPE_OPTIONS', () => {
    it('should be derived from ALARM_TYPE_MAP', () => {
      const mapKeys = Object.keys(ALARM_TYPE_MAP);
      const optionValues = ALARM_TYPE_OPTIONS.map((o) => o.value);
      expect(optionValues.sort()).toEqual(mapKeys.sort());
    });

    it('should have matching labels', () => {
      for (const opt of ALARM_TYPE_OPTIONS) {
        expect(opt.label).toBe(ALARM_TYPE_MAP[opt.value]);
      }
    });
  });
});
