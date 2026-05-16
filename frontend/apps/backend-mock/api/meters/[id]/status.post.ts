import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(async (event) => {
  return useResponseSuccess({ success: true });
});
