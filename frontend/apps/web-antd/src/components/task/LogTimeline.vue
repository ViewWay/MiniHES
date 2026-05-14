<script setup lang="ts">
import { Timeline, Tag } from 'ant-design-vue';

defineProps<{
  logs: Array<{
    time: string;
    status: string;
    message: string;
  }>;
}>();

const statusColorMap: Record<string, string> = {
  success: 'green',
  failed: 'red',
  running: 'blue',
  pending: 'gray',
};
</script>

<template>
  <Timeline>
    <Timeline.Item v-for="log in logs" :key="log.time" :color="statusColorMap[log.status] || 'gray'">
      <div style="display: flex; align-items: center; gap: 8px">
        <Tag :color="statusColorMap[log.status]">{{ log.status }}</Tag>
        <span style="color: #999; font-size: 12px">{{ log.time }}</span>
      </div>
      <div style="margin-top: 4px">{{ log.message }}</div>
    </Timeline.Item>
  </Timeline>
</template>
