import { defineStore } from 'pinia';
import { ref } from 'vue';

import {
  getTaskList,
  getTaskDetail,
  getTaskLogs,
} from '#/api/modules/task';
import type { TaskListParams } from '#/api/modules/task';

export interface TaskItem {
  id: number;
  task_name: string;
  task_type: 'cron' | 'interval' | 'once';
  status: string;
  priority?: number;
  retry_times?: number;
  timeout?: number;
  is_enabled?: boolean;
  total_devices?: number;
  success_rate?: number;
  next_execute_time?: string;
  last_execute_time?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface TaskLog {
  id: number;
  task_id: number;
  status: string;
  started_at?: string;
  finished_at?: string;
  total_devices?: number;
  success_count?: number;
  fail_count?: number;
  [key: string]: any;
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<TaskItem[]>([]);
  const total = ref(0);
  const loading = ref(false);

  const currentTask = ref<TaskItem | null>(null);
  const currentTaskLoading = ref(false);

  const taskLogs = ref<TaskLog[]>([]);
  const taskLogsTotal = ref(0);
  const taskLogsLoading = ref(false);

  async function fetchTasks(params: TaskListParams) {
    loading.value = true;
    try {
      const res = await getTaskList(params);
      tasks.value = res.items || [];
      total.value = res.total || 0;
    } finally {
      loading.value = false;
    }
  }

  async function fetchTaskDetail(id: number) {
    currentTaskLoading.value = true;
    try {
      currentTask.value = await getTaskDetail(id);
    } finally {
      currentTaskLoading.value = false;
    }
  }

  async function fetchTaskLogs(params: {
    task_id: number;
    page?: number;
    page_size?: number;
  }) {
    taskLogsLoading.value = true;
    try {
      const res = await getTaskLogs(params);
      taskLogs.value = res.items || [];
      taskLogsTotal.value = res.total || 0;
    } finally {
      taskLogsLoading.value = false;
    }
  }

  /**
   * Update a task in the local list by id.
   * Useful for real-time WebSocket updates.
   */
  function updateTaskInList(id: number, updates: Partial<TaskItem>) {
    const index = tasks.value.findIndex((t) => t.id === id);
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index]!, ...updates };
    }
  }

  return {
    // State
    tasks,
    total,
    loading,
    currentTask,
    currentTaskLoading,
    taskLogs,
    taskLogsTotal,
    taskLogsLoading,
    // Actions
    fetchTasks,
    fetchTaskDetail,
    fetchTaskLogs,
    updateTaskInList,
  };
});
