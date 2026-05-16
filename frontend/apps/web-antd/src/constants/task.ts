export const TASK_STATUS_MAP: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '待执行' },
  ready: { color: 'default', label: '就绪' },
  running: { color: 'processing', label: '执行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
  cancelled: { color: 'warning', label: '已取消' },
  paused: { color: 'orange', label: '已暂停' },
};

export const TASK_TYPE_MAP: Record<string, string> = {
  daily_read: '日常抄表',
  test_read: '测试读数',
  parameter_read: '参数读取',
  event_read: '事件读取',
  firmware_upgrade: '固件升级',
  parameter_config: '参数配置',
  cron: '定时任务',
  interval: '循环任务',
  once: '一次性任务',
};

export const TASK_CATEGORY_MAP: Record<string, { color: string; label: string }> = {
  standard: { color: 'blue', label: '标准抄表' },
  test: { color: 'purple', label: '测试任务' },
  maintenance: { color: 'orange', label: '维护任务' },
  emergency: { color: 'red', label: '紧急任务' },
  collection: { color: 'blue', label: '采集任务' },
  analysis: { color: 'purple', label: '分析任务' },
  report: { color: 'cyan', label: '报表任务' },
  cleanup: { color: 'orange', label: '清理任务' },
};

export const TASK_PRIORITY_MAP: Record<string, { color: string; label: string }> = {
  '1': { color: 'red', label: '紧急' },
  '3': { color: 'orange', label: '高' },
  '5': { color: 'blue', label: '中' },
  '7': { color: 'default', label: '低' },
  '10': { color: 'default', label: '最低' },
};

export const LOG_STATUS_MAP: Record<string, { color: string; label: string }> = {
  success: { color: 'success', label: '成功' },
  failed: { color: 'error', label: '失败' },
  timeout: { color: 'warning', label: '超时' },
  skipped: { color: 'default', label: '跳过' },
};
