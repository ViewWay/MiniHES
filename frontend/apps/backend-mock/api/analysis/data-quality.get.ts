import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.page_size) || 20;

  const qualityData = [
    { id: 1, meter_id: 1, meter_name: '三相表#1', project_id: 1, date: '2025-05-15', completeness: 99.5, accuracy: 98.2, timeliness: 100, consistency: 99.1, overall_score: 99.2 },
    { id: 2, meter_id: 2, meter_name: '三相表#2', project_id: 1, date: '2025-05-15', completeness: 98.0, accuracy: 97.5, timeliness: 99.5, consistency: 98.3, overall_score: 98.3 },
    { id: 3, meter_id: 3, meter_name: '单相表#1', project_id: 2, date: '2025-05-15', completeness: 95.2, accuracy: 96.8, timeliness: 98.0, consistency: 97.1, overall_score: 96.8 },
    { id: 4, meter_id: 4, meter_name: 'NB-IoT表#1', project_id: 3, date: '2025-05-15', completeness: 92.5, accuracy: 99.0, timeliness: 88.5, consistency: 95.2, overall_score: 93.8 },
    { id: 5, meter_id: 7, meter_name: '三相表#3', project_id: 1, date: '2025-05-15', completeness: 45.0, accuracy: 85.3, timeliness: 50.0, consistency: 60.0, overall_score: 60.1 },
    { id: 6, meter_id: 6, meter_name: 'PLC表#1', project_id: 5, date: '2025-05-15', completeness: 97.8, accuracy: 98.5, timeliness: 96.0, consistency: 98.0, overall_score: 97.6 },
    { id: 7, meter_id: 8, meter_name: '三相表#4', project_id: 1, date: '2025-05-15', completeness: 99.0, accuracy: 97.2, timeliness: 99.8, consistency: 98.5, overall_score: 98.6 },
    { id: 8, meter_id: 9, meter_name: '单相表#2', project_id: 2, date: '2025-05-15', completeness: 96.5, accuracy: 99.1, timeliness: 97.0, consistency: 99.0, overall_score: 97.9 },
  ];

  const start = (page - 1) * pageSize;
  const items = qualityData.slice(start, start + pageSize);

  return useResponseSuccess({ items, total: qualityData.length });
});
