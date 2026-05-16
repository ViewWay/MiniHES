import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({ success: true, message: '一致性检查已触发' });
});
