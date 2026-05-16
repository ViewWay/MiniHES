import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  return useResponseSuccess({ success: true, is_enabled: body.is_enabled });
});
