<script setup lang="ts">
import { Tag } from 'ant-design-vue';

const props = defineProps<{
  status: string;
  size?: 'small' | 'default';
}>();

const statusMap: Record<string, { color: string; text: string }> = {
  in_stock: { color: 'green', text: '在库' },
  testing: { color: 'blue', text: '挂表测试中' },
  test_complete: { color: 'cyan', text: '测试完成待拆' },
  borrowed: { color: 'orange', text: '借出' },
  repairing: { color: 'gold', text: '维修中' },
  scrapped: { color: 'red', text: '报废' },
};
</script>

<template>
  <Tag :color="statusMap[status]?.color" :style="{ fontSize: size === 'small' ? '11px' : '13px' }">
    {{ statusMap[status]?.text || status }}
  </Tag>
</template>
