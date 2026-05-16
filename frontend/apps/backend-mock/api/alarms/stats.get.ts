import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    total: 12,
    unhandled_count: 5,
    critical_count: 3,
    warning_count: 4,
    info_count: 5,
    active: 5,
  });
});
