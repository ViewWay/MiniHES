import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess([
    { id: 1, name: '单相电能表', code: 'single_phase', description: '220V 单相电表' },
    { id: 2, name: '三相四线电能表', code: 'three_phase_4w', description: '3×220/380V 三相四线' },
    { id: 3, name: '三相三线电能表', code: 'three_phase_3w', description: '3×100V 三相三线' },
  ]);
});
