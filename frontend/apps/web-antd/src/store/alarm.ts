import { defineStore } from 'pinia';
import { ref } from 'vue';

import {
  getAlarmList,
  handleAlarm as handleAlarmApi,
  getAlarmStats,
} from '#/api/modules/alarm';
import type { AlarmListParams } from '#/api/modules/alarm';

export interface AlarmItem {
  id: number;
  alarm_name: string;
  level: 'critical' | 'warning' | 'info';
  status: 'unhandled' | 'handled' | 'ignored';
  message: string;
  device_id?: number;
  device_name?: string;
  triggered_at: string;
  handled_at?: string;
  handled_by?: string;
  handle_remark?: string;
  created_at: string;
  [key: string]: any;
}

export interface AlarmStats {
  total: number;
  unhandled: number;
  critical: number;
  warning: number;
}

export const useAlarmStore = defineStore('alarm', () => {
  const alarms = ref<AlarmItem[]>([]);
  const total = ref(0);
  const loading = ref(false);

  const stats = ref<AlarmStats>({
    total: 0,
    unhandled: 0,
    critical: 0,
    warning: 0,
  });
  const statsLoading = ref(false);

  async function fetchAlarms(params?: AlarmListParams) {
    loading.value = true;
    try {
      const res = await getAlarmList(params);
      alarms.value = res.items || [];
      total.value = res.total || 0;
    } finally {
      loading.value = false;
    }
  }

  async function handleAlarm(
    id: number,
    data: { handle_notes: string },
  ) {
    const res = await handleAlarmApi(id, data);
    // Update the alarm in the local list
    const index = alarms.value.findIndex((a) => a.id === id);
    if (index !== -1) {
      alarms.value[index] = { ...alarms.value[index]!, status: 'handled' };
    }
    // Refresh stats after handling
    await fetchAlarmStats();
    return res;
  }

  async function fetchAlarmStats() {
    statsLoading.value = true;
    try {
      stats.value = await getAlarmStats();
    } finally {
      statsLoading.value = false;
    }
  }

  return {
    // State
    alarms,
    total,
    loading,
    stats,
    statsLoading,
    // Actions
    fetchAlarms,
    handleAlarm,
    fetchAlarmStats,
  };
});
