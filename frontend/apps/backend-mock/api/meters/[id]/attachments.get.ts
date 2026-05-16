import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess([
    { id: 1, filename: '出厂检测报告.pdf', size: 1024000, uploaded_at: '2024-04-02 10:00:00' },
    { id: 2, filename: '通信测试记录.xlsx', size: 256000, uploaded_at: '2024-04-20 14:00:00' },
  ]);
});
