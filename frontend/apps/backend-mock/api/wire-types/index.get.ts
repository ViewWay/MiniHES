import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess([
    { id: 1, name: '单相二线', code: '1p2w' },
    { id: 2, name: '三相三线', code: '3p3w' },
    { id: 3, name: '三相四线', code: '3p4w' },
  ]);
});
