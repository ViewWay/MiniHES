import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, title: '三相表型式评价测试报告', project_id: 1, type: 'type_approval', status: 'completed', created_at: '2025-05-15 10:00:00' },
      { id: 2, title: '单相表协议一致性报告', project_id: 2, type: 'protocol_conformance', status: 'generating', created_at: '2025-05-14 08:00:00' },
      { id: 3, title: 'NB-IoT稳定性周报', project_id: 3, type: 'stability', status: 'completed', created_at: '2025-05-13 10:00:00' },
    ],
    total: 3,
  });
});
