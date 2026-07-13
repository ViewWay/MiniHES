import { defineStore } from 'pinia';
import { ref } from 'vue';

import {
  getMeterList,
  getMeterDetail,
  getMeterStatusHistory,
  getBorrowRecords,
  changeMeterStatus,
} from '#/api/modules/meter';
import type { MeterListParams } from '#/api/modules/meter';
import { getProjectList, getMeterTypes, getWireTypes } from '#/api/modules/project';
import type { MeterType, Project, WireType } from '#/api/modules/project';

export interface MeterItem {
  id: number;
  serial_number: string;
  meter_name: string;
  meter_type_id: number;
  project_id: number;
  protocol: string;
  line_type: string;
  status: string;
  manufacturer?: string;
  model?: string;
  firmware_version?: string;
  hardware_version?: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface BorrowRecord {
  id: number;
  meter_id: number;
  borrower_name: string;
  expected_return_date: string;
  borrow_reason: string;
  status: string;
  created_at?: string;
  [key: string]: any;
}

export interface StatusHistory {
  id: number;
  meter_id: number;
  from_status: string;
  to_status: string;
  reason: string;
  operated_at: string;
  [key: string]: any;
}

export const useMeterStore = defineStore('meter', () => {
  const meters = ref<MeterItem[]>([]);
  const currentMeter = ref<MeterItem | null>(null);
  const total = ref(0);
  const loading = ref(false);

  // Cache: meter types
  const meterTypes = ref<MeterType[]>([]);
  const meterTypesLoading = ref(false);

  // Cache: projects
  const projects = ref<Project[]>([]);
  const projectsLoading = ref(false);

  // Cache: wire types
  const wireTypes = ref<WireType[]>([]);
  const wireTypesLoading = ref(false);

  // Borrow records
  const borrowRecords = ref<BorrowRecord[]>([]);
  const borrowRecordsLoading = ref(false);

  // Status history
  const statusHistory = ref<StatusHistory[]>([]);
  const statusHistoryLoading = ref(false);

  async function fetchMeters(params: MeterListParams) {
    loading.value = true;
    try {
      const res = await getMeterList(params);
      meters.value = res.items || [];
      total.value = res.total || 0;
    } finally {
      loading.value = false;
    }
  }

  async function fetchMeterDetail(id: number) {
    loading.value = true;
    try {
      currentMeter.value = await getMeterDetail(id);
    } finally {
      loading.value = false;
    }
  }

  async function fetchMeterTypes() {
    if (meterTypes.value.length > 0) return;
    meterTypesLoading.value = true;
    try {
      const res = await getMeterTypes();
      meterTypes.value = res.items || res || [];
    } finally {
      meterTypesLoading.value = false;
    }
  }

  async function fetchProjects() {
    if (projects.value.length > 0) return;
    projectsLoading.value = true;
    try {
      const res = await getProjectList();
      projects.value = res.items || res || [];
    } finally {
      projectsLoading.value = false;
    }
  }

  async function fetchWireTypes() {
    if (wireTypes.value.length > 0) return;
    wireTypesLoading.value = true;
    try {
      const res = await getWireTypes();
      wireTypes.value = res.items || res || [];
    } finally {
      wireTypesLoading.value = false;
    }
  }

  async function fetchBorrowRecords(params?: {
    meter_id?: number;
    status?: string;
  }) {
    borrowRecordsLoading.value = true;
    try {
      const res = await getBorrowRecords(params);
      borrowRecords.value = res.items || res || [];
    } finally {
      borrowRecordsLoading.value = false;
    }
  }

  async function fetchStatusHistory(
    id: number,
    _params?: { page?: number; page_size?: number },
  ) {
    statusHistoryLoading.value = true;
    try {
      const res = await getMeterStatusHistory(id);
      statusHistory.value = Array.isArray(res) ? res : res.items || [];
    } finally {
      statusHistoryLoading.value = false;
    }
  }

  async function updateMeterStatus(
    id: number,
    data: { status: string; reason: string },
  ) {
    const res = await changeMeterStatus(id, data);
    await fetchMeterDetail(id);
    return res;
  }

  return {
    // State
    meters,
    currentMeter,
    total,
    loading,
    meterTypes,
    meterTypesLoading,
    projects,
    projectsLoading,
    wireTypes,
    wireTypesLoading,
    borrowRecords,
    borrowRecordsLoading,
    statusHistory,
    statusHistoryLoading,
    // Actions
    fetchMeters,
    fetchMeterDetail,
    fetchMeterTypes,
    fetchProjects,
    fetchWireTypes,
    fetchBorrowRecords,
    fetchStatusHistory,
    updateMeterStatus,
  };
});
