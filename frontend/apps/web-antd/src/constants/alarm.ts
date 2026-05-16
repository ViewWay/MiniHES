export const ALARM_SEVERITY_MAP: Record<string, { color: string; label: string }> = {
  critical: { color: 'red', label: '严重' },
  warning: { color: 'orange', label: '警告' },
  info: { color: 'blue', label: '信息' },
};

export const ALARM_TYPE_MAP: Record<string, string> = {
  threshold: '阈值告警',
  anomaly: '数据异常',
  communication: '通信告警',
  stack: '堆栈告警',
  eeprom: 'EEPROM告警',
};

export const ALARM_SEVERITY_OPTIONS = [
  { value: 'critical', label: '严重' },
  { value: 'warning', label: '警告' },
  { value: 'info', label: '信息' },
];

export const ALARM_TYPE_OPTIONS = Object.entries(ALARM_TYPE_MAP).map(
  ([value, label]) => ({ value, label }),
);
