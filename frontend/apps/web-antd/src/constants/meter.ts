export interface StatusOption {
  color: string;
  label: string;
}

export const METER_STATUS_MAP: Record<string, StatusOption> = {
  in_stock: { color: 'default', label: '在库' },
  testing: { color: 'blue', label: '挂表测试中' },
  field_deployed: { color: 'green', label: '现场运行' },
  borrowed: { color: 'orange', label: '借用中' },
  returned: { color: 'cyan', label: '已归还' },
  maintenance: { color: 'red', label: '维修中' },
  scrapped: { color: 'default', label: '已报废' },
  pending_test: { color: 'purple', label: '待测试' },
  test_passed: { color: 'success', label: '测试通过' },
  test_failed: { color: 'error', label: '测试不通过' },
};

export const METER_TYPE_MAP: Record<string, string> = {
  single_phase: '单相表',
  three_phase: '三相表',
  multi_function: '多功能表',
  smart: '智能表',
};

export const PROTOCOL_OPTIONS = [
  { label: 'DLMS/COSEM', value: 'dlms_cosem' },
  { label: 'DLMS/COSEM (红外)', value: 'dlms_cosem_ir' },
  { label: 'Modbus RTU', value: 'modbus_rtu' },
  { label: 'Modbus TCP', value: 'modbus_tcp' },
  { label: 'MQTT', value: 'mqtt' },
];

export const COMMUNICATION_TYPE_MAP: Record<string, string> = {
  infrared: '红外',
  cellular_4g: '4G/5G',
  nb_iot: 'NB-IoT',
  m_bus: 'M-Bus',
  lora: 'LoRaWAN',
  g3_plc: 'G3-PLC',
  tcp: 'TCP/IP',
  serial: '串口',
};

export const STATUS_FLOW_OPTIONS = [
  { from: 'in_stock', to: 'testing', label: '挂表测试' },
  { from: 'testing', to: 'test_passed', label: '测试通过' },
  { from: 'testing', to: 'test_failed', label: '测试不通过' },
  { from: 'test_passed', to: 'field_deployed', label: '部署到现场' },
  { from: 'test_failed', to: 'in_stock', label: '退回库存' },
  { from: 'field_deployed', to: 'maintenance', label: '送修' },
  { from: 'maintenance', to: 'in_stock', label: '修好入库' },
  { from: 'maintenance', to: 'scrapped', label: '报废' },
  { from: 'field_deployed', to: 'in_stock', label: '撤回入库' },
];
