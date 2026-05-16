import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  return useResponseSuccess({ ...body });
});
