import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  return useResponseSuccess({
    id,
    serial_number: `SM-2024-${String(id).padStart(4, '0')}`,
    meter_name: `样机#${id}`,
    meter_type_id: 2,
    project_id: 1,
    protocol: 'DLMS',
    line_type: '3p4w',
    manufacturer: '华立科技',
    model: 'HL316-3P',
    firmware_version: 'v2.1.0',
    hardware_version: 'HW3.0',
    frame_number: `FN-${String(id).padStart(3, '0')}`,
    location: `A区-${String(id).padStart(2, '0')}工位`,
    status: 'in_use',
    factory_date: '2024-03-15',
    purchase_date: '2024-04-01',
    warranty_date: '2027-04-01',
    notes: '',
  });
});
