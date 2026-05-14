<script setup lang="ts">
import { Progress } from 'ant-design-vue';

defineProps<{
  total: number;
  success: number;
  failed: number;
}>();
</script>

<template>
  <div>
    <Progress :percent="total > 0 ? Math.round((success / total) * 100) : 0"
      :stroke-color="failed === 0 ? '#52c41a' : '#faad14'" :size="'small'" />
    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #999">
      <span>成功: {{ success }}</span>
      <span>失败: {{ failed }}</span>
      <span>总计: {{ total }}</span>
    </div>
  </div>
</template>
