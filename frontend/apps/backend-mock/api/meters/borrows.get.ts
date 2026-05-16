import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, meter_id: 5, meter_name: '红外表#1', borrower_name: '张工程师', borrow_reason: '现场测试需要', expected_return_date: '2025-03-01', status: 'returned', created_at: '2025-02-01 09:00:00' },
      { id: 2, meter_id: 12, meter_name: '维修中表#1', borrower_name: '李测试员', borrow_reason: '维修检测', expected_return_date: '2025-05-20', status: 'active', created_at: '2025-05-10 14:30:00' },
    ],
    total: 2,
  });
});
