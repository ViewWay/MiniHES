<script setup lang="ts">
import { Card, Descriptions, DescriptionsItem, Tooltip } from 'ant-design-vue';
import StatusBadge from './StatusBadge.vue';

defineProps<{
  meter: {
    id: number;
    serial_number: string;
    meter_name: string;
    meter_type?: string;
    project_name?: string;
    protocol?: string;
    current_status: string;
    location?: string;
    online_status?: 'online' | 'offline';
  };
}>();

const emit = defineEmits<{ click: [id: number] }>();
</script>

<template>
  <Card
    hoverable
    size="small"
    @click="emit('click', meter.id)"
    style="cursor: pointer"
  >
    <template #title>
      <span style="display: inline-flex; align-items: center; gap: 8px">
        <Tooltip
          :title="meter.online_status === 'online' ? '在线' : '离线'"
        >
          <span
            :style="{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor:
                meter.online_status === 'online' ? '#52c41a' : '#ff4d4f',
              boxShadow:
                meter.online_status === 'online'
                  ? '0 0 4px #52c41a'
                  : 'none',
            }"
          />
        </Tooltip>
        <span>{{ meter.meter_name }}</span>
      </span>
    </template>
    <template #extra>
      <StatusBadge :status="meter.current_status" size="small" />
    </template>
    <Descriptions :column="1" size="small">
      <DescriptionsItem label="编号">
        {{ meter.serial_number }}
      </DescriptionsItem>
      <DescriptionsItem label="项目">
        {{ meter.project_name || '-' }}
      </DescriptionsItem>
      <DescriptionsItem label="协议">
        {{ meter.protocol || '-' }}
      </DescriptionsItem>
    </Descriptions>
  </Card>
</template>
