import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler((event) => {
  return useResponseSuccess({ success: true });
});
