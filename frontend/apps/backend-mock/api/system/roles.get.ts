import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    items: [
      { id: 1, name: '超级管理员', code: 'super', description: '系统超级管理员，拥有所有权限', permission_ids: [1, 2, 3, 4, 5, 6, 7, 8], user_count: 1 },
      { id: 2, name: '工程师', code: 'admin', description: '测试工程师，可管理设备和任务', permission_ids: [1, 2, 3, 4], user_count: 2 },
      { id: 3, name: '测试员', code: 'user', description: '普通测试员，可查看数据和报告', permission_ids: [1, 2], user_count: 2 },
    ],
    total: 3,
  });
});
