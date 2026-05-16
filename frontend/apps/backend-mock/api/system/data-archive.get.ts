import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;

  const archives = [
    { id: 1, archive_type: 'auto', table_name: 'meter_readings', days_to_archive: 90, archived_count: 125000, status: 'completed', created_at: '2025-05-01 02:00:00' },
    { id: 2, archive_type: 'auto', table_name: 'alarm_logs', days_to_archive: 180, archived_count: 8500, status: 'completed', created_at: '2025-04-01 02:00:00' },
    { id: 3, archive_type: 'auto', table_name: 'task_logs', days_to_archive: 60, archived_count: 32000, status: 'completed', created_at: '2025-03-01 02:00:00' },
  ];

  const start = (page - 1) * pageSize;
  const items = archives.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: archives.length });
});
