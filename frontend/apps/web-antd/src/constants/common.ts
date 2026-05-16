export const DEFAULT_PAGE_SIZE = 20;
export const METADATA_FETCH_SIZE = 200;

export const POLL_INTERVALS = {
  ALARM: 30_000,
  TASK_MONITOR: 5_000,
  TASK_LOGS: 10_000,
  HEALTH: 15_000,
  DB_MONITOR: 30_000,
  METER_REALTIME: 3_000,
} as const;

export const THEME_COLORS = {
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#ff4d4f',
  PROCESSING: '#1890ff',
  ORANGE: '#fa8c16',
  PURPLE: '#722ed1',
  TEXT_SECONDARY: '#999999',
  TEXT_TERTIARY: '#666666',
} as const;
