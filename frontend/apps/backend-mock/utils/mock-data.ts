export interface UserInfo {
  id: number;
  password: string;
  realName: string;
  roles: string[];
  username: string;
  homePath?: string;
}

export interface TimezoneOption {
  offset: number;
  timezone: string;
}

export const MOCK_USERS: UserInfo[] = [
  {
    id: 0,
    password: '123456',
    realName: '超级管理员',
    roles: ['super'],
    username: 'admin',
  },
  {
    id: 1,
    password: '123456',
    realName: '张工程师',
    roles: ['admin'],
    username: 'engineer',
    homePath: '/analytics',
  },
  {
    id: 2,
    password: '123456',
    realName: '李测试员',
    roles: ['user'],
    username: 'tester',
    homePath: '/dashboard',
  },
];

export const MOCK_CODES = [
  {
    codes: ['AC_100100', 'AC_100110', 'AC_100120', 'AC_100010'],
    username: 'admin',
  },
  {
    codes: ['AC_100010', 'AC_100020', 'AC_100030'],
    username: 'engineer',
  },
  {
    codes: ['AC_1000001', 'AC_1000002'],
    username: 'tester',
  },
];

// ========== MiniHES 业务模拟数据 ==========

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => {
  const d = new Date(now);
  d.setDate(d.getDate() - n);
  return d;
};

// --- 项目 ---
export const MOCK_PROJECTS = [
  { id: 1, name: '三相智能电能表型式评价测试', description: '某厂商三相表全性能测试', test_leader: '张工程师', dev_leader: '王研发', status: 'testing', device_count: 24, online_count: 20, created_at: fmtDate(daysAgo(30)) },
  { id: 2, name: '单相费控智能表通信协议一致性测试', description: '单相表DLMS协议一致性验证', test_leader: '李测试员', dev_leader: '赵开发', status: 'active', device_count: 12, online_count: 10, created_at: fmtDate(daysAgo(15)) },
  { id: 3, name: 'NB-IoT电表数据采集稳定性测试', description: 'NB-IoT通信模块长期稳定性', test_leader: '张工程师', dev_leader: '刘硬件', status: 'testing', device_count: 8, online_count: 8, created_at: fmtDate(daysAgo(7)) },
  { id: 4, name: '红外抄表功能验证', description: '红外通信接口功能验证', test_leader: '李测试员', dev_leader: '陈固件', status: 'completed', device_count: 6, online_count: 0, created_at: fmtDate(daysAgo(45)) },
  { id: 5, name: 'G3-PLC载波通信性能测试', description: '电力线载波通信性能测试', test_leader: '张工程师', dev_leader: '王研发', status: 'active', device_count: 16, online_count: 14, created_at: fmtDate(daysAgo(5)) },
];

// --- 电表类型 / 接线方式 ---
export const MOCK_METER_TYPES = [
  { id: 1, name: '单相电能表', code: 'single_phase', description: '220V 单相电表' },
  { id: 2, name: '三相四线电能表', code: 'three_phase_4w', description: '3×220/380V 三相四线' },
  { id: 3, name: '三相三线电能表', code: 'three_phase_3w', description: '3×100V 三相三线' },
];

export const MOCK_WIRE_TYPES = [
  { id: 1, name: '单相二线', code: '1p2w' },
  { id: 2, name: '三相三线', code: '3p3w' },
  { id: 3, name: '三相四线', code: '3p4w' },
];

// --- 设备/样机 ---
export const MOCK_METERS = [
  { id: 1, serial_number: 'SM-2024-0001', meter_name: '三相表#1', meter_type_id: 2, project_id: 1, protocol: 'DLMS', line_type: '3p4w', manufacturer: '华立科技', model: 'HL316-3P', firmware_version: 'v2.1.0', hardware_version: 'HW3.0', frame_number: 'FN-001', location: 'A区-01工位', status: 'in_use', factory_date: '2024-03-15', purchase_date: '2024-04-01', warranty_date: '2027-04-01', notes: '' },
  { id: 2, serial_number: 'SM-2024-0002', meter_name: '三相表#2', meter_type_id: 2, project_id: 1, protocol: 'DLMS', line_type: '3p4w', manufacturer: '华立科技', model: 'HL316-3P', firmware_version: 'v2.1.0', hardware_version: 'HW3.0', frame_number: 'FN-002', location: 'A区-02工位', status: 'in_use', factory_date: '2024-03-15', purchase_date: '2024-04-01', warranty_date: '2027-04-01', notes: '' },
  { id: 3, serial_number: 'SM-2024-0003', meter_name: '单相表#1', meter_type_id: 1, project_id: 2, protocol: 'DLMS', line_type: '1p2w', manufacturer: '威胜集团', model: 'WS-D112', firmware_version: 'v1.3.2', hardware_version: 'HW2.1', frame_number: 'FN-003', location: 'B区-01工位', status: 'in_use', factory_date: '2024-05-10', purchase_date: '2024-06-01', warranty_date: '2027-06-01', notes: '' },
  { id: 4, serial_number: 'SM-2024-0004', meter_name: 'NB-IoT表#1', meter_type_id: 1, project_id: 3, protocol: 'DLMS', line_type: '1p2w', manufacturer: '海兴电力', model: 'HX-NB01', firmware_version: 'v3.0.1', hardware_version: 'HW1.0', frame_number: 'FN-004', location: 'C区-01工位', status: 'online', factory_date: '2024-07-20', purchase_date: '2024-08-01', warranty_date: '2027-08-01', notes: 'NB-IoT模块' },
  { id: 5, serial_number: 'SM-2024-0005', meter_name: '红外表#1', meter_type_id: 1, project_id: 4, protocol: 'DLMS', line_type: '1p2w', manufacturer: '许继电气', model: 'XJ-IR200', firmware_version: 'v1.0.5', hardware_version: 'HW1.2', frame_number: 'FN-005', location: 'D区-01工位', status: 'returned', factory_date: '2024-01-10', purchase_date: '2024-02-01', warranty_date: '2027-02-01', notes: '红外通信' },
  { id: 6, serial_number: 'SM-2024-0006', meter_name: 'PLC表#1', meter_type_id: 2, project_id: 5, protocol: 'DLMS', line_type: '3p4w', manufacturer: '林洋能源', model: 'LY-PLC100', firmware_version: 'v2.5.0', hardware_version: 'HW4.0', frame_number: 'FN-006', location: 'E区-01工位', status: 'in_use', factory_date: '2024-09-01', purchase_date: '2024-09-15', warranty_date: '2027-09-15', notes: 'G3-PLC模块' },
  { id: 7, serial_number: 'SM-2024-0007', meter_name: '三相表#3', meter_type_id: 2, project_id: 1, protocol: 'DLMS', line_type: '3p4w', manufacturer: '华立科技', model: 'HL316-3P', firmware_version: 'v2.1.0', hardware_version: 'HW3.0', frame_number: 'FN-007', location: 'A区-03工位', status: 'offline', factory_date: '2024-03-15', purchase_date: '2024-04-01', warranty_date: '2027-04-01', notes: '当前离线' },
  { id: 8, serial_number: 'SM-2024-0008', meter_name: '三相表#4', meter_type_id: 3, project_id: 1, protocol: 'DLMS', line_type: '3p3w', manufacturer: '威胜集团', model: 'WS-D316', firmware_version: 'v2.0.3', hardware_version: 'HW2.5', frame_number: 'FN-008', location: 'A区-04工位', status: 'in_use', factory_date: '2024-06-20', purchase_date: '2024-07-01', warranty_date: '2027-07-01', notes: '' },
  { id: 9, serial_number: 'SM-2024-0009', meter_name: '单相表#2', meter_type_id: 1, project_id: 2, protocol: 'DLMS', line_type: '1p2w', manufacturer: '海兴电力', model: 'HX-D112', firmware_version: 'v1.5.0', hardware_version: 'HW1.8', frame_number: 'FN-009', location: 'B区-02工位', status: 'in_use', factory_date: '2024-08-05', purchase_date: '2024-08-15', warranty_date: '2027-08-15', notes: '' },
  { id: 10, serial_number: 'SM-2024-0010', meter_name: 'NB-IoT表#2', meter_type_id: 1, project_id: 3, protocol: 'DLMS', line_type: '1p2w', manufacturer: '许继电气', model: 'XJ-NB200', firmware_version: 'v3.1.0', hardware_version: 'HW1.2', frame_number: 'FN-010', location: 'C区-02工位', status: 'online', factory_date: '2024-09-10', purchase_date: '2024-09-20', warranty_date: '2027-09-20', notes: '' },
  { id: 11, serial_number: 'SM-2024-0011', meter_name: 'PLC表#2', meter_type_id: 2, project_id: 5, protocol: 'DLMS', line_type: '3p4w', manufacturer: '林洋能源', model: 'LY-PLC100', firmware_version: 'v2.5.0', hardware_version: 'HW4.0', frame_number: 'FN-011', location: 'E区-02工位', status: 'in_use', factory_date: '2024-09-01', purchase_date: '2024-09-15', warranty_date: '2027-09-15', notes: '' },
  { id: 12, serial_number: 'SM-2024-0012', meter_name: '维修中表#1', meter_type_id: 1, project_id: 1, protocol: 'DLMS', line_type: '1p2w', manufacturer: '华立科技', model: 'HL112', firmware_version: 'v1.2.0', hardware_version: 'HW2.0', frame_number: 'FN-012', location: '维修室', status: 'repairing', factory_date: '2023-06-15', purchase_date: '2023-07-01', warranty_date: '2026-07-01', notes: '显示模块故障' },
];

// --- 采集任务 ---
export const MOCK_TASKS = [
  { id: 1, task_name: '三相表每日数据采集', task_category: 'collection', task_type: 'cron', schedule_config: { cron: '0 8 * * *' }, execution_content: { meter_ids: [1, 2, 7, 8], obis_codes: ['1.0.0.0.0.255', '1.0.12.7.0.255', '1.0.21.7.0.255'] }, filter_config: {}, priority: 1, retry_times: 3, timeout: 60, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(20)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(daysAgo(-1)), today_executions: 4 },
  { id: 2, task_name: '单相表负荷曲线采集', task_category: 'collection', task_type: 'interval', schedule_config: { interval_minutes: 30 }, execution_content: { meter_ids: [3, 9], obis_codes: ['1.0.1.8.0.255'] }, filter_config: {}, priority: 2, retry_times: 2, timeout: 30, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(15)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(new Date(now.getTime() + 30 * 60_000)), today_executions: 8 },
  { id: 3, task_name: 'NB-IoT实时监控', task_category: 'collection', task_type: 'interval', schedule_config: { interval_minutes: 15 }, execution_content: { meter_ids: [4, 10], obis_codes: ['1.0.0.0.0.255'] }, filter_config: {}, priority: 1, retry_times: 5, timeout: 20, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(7)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(new Date(now.getTime() + 15 * 60_000)), today_executions: 16 },
  { id: 4, task_name: '数据一致性分析', task_category: 'analysis', task_type: 'cron', schedule_config: { cron: '0 2 * * *' }, execution_content: { analysis_type: 'consistency' }, filter_config: {}, priority: 3, retry_times: 1, timeout: 300, is_enabled: true, status: 'completed', created_at: fmtDate(daysAgo(10)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(daysAgo(-1)), today_executions: 1 },
  { id: 5, task_name: 'PLC载波稳定性测试', task_category: 'collection', task_type: 'cron', schedule_config: { cron: '0 */2 * * *' }, execution_content: { meter_ids: [6, 11], obis_codes: ['1.0.0.0.0.255', '0.0.1.0.0.255'] }, filter_config: {}, priority: 2, retry_times: 3, timeout: 45, is_enabled: true, status: 'running', created_at: fmtDate(daysAgo(5)), last_run: fmtDate(daysAgo(0)), next_run: fmtDate(new Date(now.getTime() + 2 * 3600_000)), today_executions: 6 },
  { id: 6, task_name: '每周测试报告生成', task_category: 'report', task_type: 'cron', schedule_config: { cron: '0 9 * * 1' }, execution_content: { report_type: 'weekly' }, filter_config: { project_ids: [1, 2] }, priority: 5, retry_times: 1, timeout: 600, is_enabled: false, status: 'paused', created_at: fmtDate(daysAgo(30)), last_run: fmtDate(daysAgo(3)), next_run: null, today_executions: 0 },
];

// --- 告警 ---
export const MOCK_ALARMS = [
  { id: 1, meter_id: 7, meter_name: '三相表#3', alarm_type: 'communication', severity: 'critical', alarm_message: '设备持续离线超过30分钟', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(0)) },
  { id: 2, meter_id: 12, meter_name: '维修中表#1', alarm_type: 'eeprom', severity: 'warning', alarm_message: 'EEPROM校验失败', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(0)) },
  { id: 3, meter_id: 1, meter_name: '三相表#1', alarm_type: 'threshold', severity: 'warning', alarm_message: '相位A电压超过上限阈值', alarm_value: '245.8V', threshold_value: '240V', is_handled: true, handle_notes: '确认是测试工况，正常', created_at: fmtDate(daysAgo(1)) },
  { id: 4, meter_id: 3, meter_name: '单相表#1', alarm_type: 'anomaly', severity: 'info', alarm_message: '电流读数突变，疑似负荷变化', alarm_value: '15.2A', threshold_value: null, is_handled: true, handle_notes: '正常负荷切换', created_at: fmtDate(daysAgo(1)) },
  { id: 5, meter_id: 2, meter_name: '三相表#2', alarm_type: 'threshold', severity: 'critical', alarm_message: '总功率超过额定值', alarm_value: '12.5kW', threshold_value: '10kW', is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(1)) },
  { id: 6, meter_id: 4, meter_name: 'NB-IoT表#1', alarm_type: 'communication', severity: 'warning', alarm_message: 'NB-IoT信号强度低于阈值', alarm_value: '-120dBm', threshold_value: '-110dBm', is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(2)) },
  { id: 7, meter_id: 6, meter_name: 'PLC表#1', alarm_type: 'stack', severity: 'info', alarm_message: 'PLC载波通信重试次数增加', alarm_value: '5次', threshold_value: '3次', is_handled: true, handle_notes: '线路噪声导致，已恢复', created_at: fmtDate(daysAgo(2)) },
  { id: 8, meter_id: 8, meter_name: '三相表#4', alarm_type: 'anomaly', severity: 'warning', alarm_message: '电能计量数据跳变', alarm_value: '5.2kWh', threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(3)) },
  { id: 9, meter_id: 9, meter_name: '单相表#2', alarm_type: 'threshold', severity: 'info', alarm_message: '当前需量接近上限', alarm_value: '8.5kW', threshold_value: '10kW', is_handled: true, handle_notes: '已记录', created_at: fmtDate(daysAgo(3)) },
  { id: 10, meter_id: 10, meter_name: 'NB-IoT表#2', alarm_type: 'communication', severity: 'critical', alarm_message: '数据上报超时', alarm_value: null, threshold_value: null, is_handled: false, handle_notes: null, created_at: fmtDate(daysAgo(4)) },
];

// --- 测试任务 ---
export const MOCK_TESTS = [
  { id: 1, project_id: 1, test_type: 'type_approval', status: 'in_progress', device_count: 24, description: '三相智能电能表型式评价全性能测试', created_at: fmtDate(daysAgo(25)), started_at: fmtDate(daysAgo(23)) },
  { id: 2, project_id: 2, test_type: 'protocol_conformance', status: 'in_progress', device_count: 12, description: 'DLMS/COSEM协议一致性验证', created_at: fmtDate(daysAgo(12)), started_at: fmtDate(daysAgo(10)) },
  { id: 3, project_id: 3, test_type: 'stability', status: 'in_progress', device_count: 8, description: 'NB-IoT通信长期稳定性测试', created_at: fmtDate(daysAgo(5)), started_at: fmtDate(daysAgo(5)) },
  { id: 4, project_id: 4, test_type: 'functional', status: 'completed', device_count: 6, description: '红外抄表功能验证', created_at: fmtDate(daysAgo(40)), started_at: fmtDate(daysAgo(38)) },
  { id: 5, project_id: 5, test_type: 'performance', status: 'pending', device_count: 16, description: 'G3-PLC载波通信性能测试', created_at: fmtDate(daysAgo(3)), started_at: null },
];

// --- 采集点配置 ---
export const MOCK_METER_POINTS = [
  { id: 1, name: '正向有功总电能', code: '1.0.0.0.0.255', unit: 'kWh', protocol: 'DLMS', description: '累积正向有功电能' },
  { id: 2, name: '当前需量', code: '1.0.1.8.0.255', unit: 'kW', protocol: 'DLMS', description: '当前15分钟需量' },
  { id: 3, name: 'A相电压', code: '1.0.12.7.0.255', unit: 'V', protocol: 'DLMS', description: '相位A电压有效值' },
  { id: 4, name: 'A相电流', code: '1.0.21.7.0.255', unit: 'A', protocol: 'DLMS', description: '相位A电流有效值' },
  { id: 5, name: 'B相电压', code: '1.0.32.7.0.255', unit: 'V', protocol: 'DLMS', description: '相位B电压有效值' },
  { id: 6, name: 'B相电流', code: '1.0.41.7.0.255', unit: 'A', protocol: 'DLMS', description: '相位B电流有效值' },
  { id: 7, name: '电表状态', code: '0.0.1.0.0.255', unit: '', protocol: 'DLMS', description: '电表运行状态字' },
  { id: 8, name: '频率', code: '1.0.14.7.0.255', unit: 'Hz', protocol: 'DLMS', description: '电网频率' },
  { id: 9, name: '功率因数', code: '1.0.13.7.0.255', unit: '', protocol: 'DLMS', description: '总功率因数' },
  { id: 10, name: '正向有功电能（费率1）', code: '1.0.1.8.1.255', unit: 'kWh', protocol: 'DLMS', description: '尖时段电能' },
];

// --- 菜单 ---
const dashboardMenus = [
  {
    meta: {
      order: -1,
      title: 'page.dashboard.title',
    },
    name: 'Dashboard',
    path: '/dashboard',
    redirect: '/analytics',
    children: [
      {
        name: 'Analytics',
        path: '/analytics',
        component: '/dashboard/analytics/index',
        meta: {
          affixTab: true,
          title: 'page.dashboard.analytics',
        },
      },
      {
        name: 'Workspace',
        path: '/workspace',
        component: '/dashboard/workspace/index',
        meta: {
          title: 'page.dashboard.workspace',
        },
      },
    ],
  },
];

export const MOCK_MENUS = [
  {
    menus: [...dashboardMenus],
    username: 'admin',
  },
  {
    menus: [...dashboardMenus],
    username: 'engineer',
  },
  {
    menus: [...dashboardMenus],
    username: 'tester',
  },
];

export const MOCK_MENU_LIST = [
  {
    id: 1,
    name: 'Workspace',
    status: 1,
    type: 'menu',
    icon: 'mdi:dashboard',
    path: '/workspace',
    component: '/dashboard/workspace/index',
    meta: {
      icon: 'carbon:workspace',
      title: 'page.dashboard.workspace',
      affixTab: true,
      order: 0,
    },
  },
];

export function getMenuIds(menus: any[]) {
  const ids: number[] = [];
  menus.forEach((item) => {
    ids.push(item.id);
    if (item.children && item.children.length > 0) {
      ids.push(...getMenuIds(item.children));
    }
  });
  return ids;
}

export const TIME_ZONE_OPTIONS: TimezoneOption[] = [
  {
    offset: -5,
    timezone: 'America/New_York',
  },
  {
    offset: 0,
    timezone: 'Europe/London',
  },
  {
    offset: 8,
    timezone: 'Asia/Shanghai',
  },
  {
    offset: 9,
    timezone: 'Asia/Tokyo',
  },
  {
    offset: 9,
    timezone: 'Asia/Seoul',
  },
];
