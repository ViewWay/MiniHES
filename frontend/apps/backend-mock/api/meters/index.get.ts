import { useResponseSuccess } from '~/utils/response';

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000);

const meters = [
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

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;
  const projectId = query.project_id as string | undefined;
  const status = query.status as string | undefined;
  const keyword = query.keyword as string | undefined;

  let filtered = [...meters];

  if (projectId) {
    filtered = filtered.filter((m) => m.project_id === Number(projectId));
  }
  if (status) {
    filtered = filtered.filter((m) => m.status === status);
  }
  if (keyword) {
    const kw = keyword.toLowerCase();
    filtered = filtered.filter(
      (m) =>
        m.meter_name.toLowerCase().includes(kw) ||
        m.serial_number.toLowerCase().includes(kw) ||
        (m.manufacturer && m.manufacturer.toLowerCase().includes(kw)),
    );
  }

  const onlineCount = filtered.filter(
    (m) => m.status === 'online' || m.status === 'in_use',
  ).length;
  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: filtered.length, online_count: onlineCount });
});
