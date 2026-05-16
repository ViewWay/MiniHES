import { useResponseSuccess } from '~/utils/response';

const now = new Date();
const fmtDate = (d: Date) => d.toISOString().replace('T', ' ').slice(0, 19);
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000);

const projects = [
  { id: 1, name: '三相智能电能表型式评价测试', description: '某厂商三相表全性能测试', test_leader: '张工程师', dev_leader: '王研发', status: 'testing', device_count: 24, online_count: 20, progress: 68, created_at: fmtDate(daysAgo(30)) },
  { id: 2, name: '单相费控智能表通信协议一致性测试', description: '单相表DLMS协议一致性验证', test_leader: '李测试员', dev_leader: '赵开发', status: 'active', device_count: 12, online_count: 10, progress: 45, created_at: fmtDate(daysAgo(15)) },
  { id: 3, name: 'NB-IoT电表数据采集稳定性测试', description: 'NB-IoT通信模块长期稳定性', test_leader: '张工程师', dev_leader: '刘硬件', status: 'testing', device_count: 8, online_count: 8, progress: 80, created_at: fmtDate(daysAgo(7)) },
  { id: 4, name: '红外抄表功能验证', description: '红外通信接口功能验证', test_leader: '李测试员', dev_leader: '陈固件', status: 'completed', device_count: 6, online_count: 0, progress: 100, created_at: fmtDate(daysAgo(45)) },
  { id: 5, name: 'G3-PLC载波通信性能测试', description: '电力线载波通信性能测试', test_leader: '张工程师', dev_leader: '王研发', status: 'active', device_count: 16, online_count: 14, progress: 25, created_at: fmtDate(daysAgo(5)) },
];

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const keyword = query.keyword as string | undefined;

  let filtered = [...projects];
  if (keyword) {
    const kw = keyword.toLowerCase();
    filtered = filtered.filter((p) => p.name.toLowerCase().includes(kw));
  }

  return useResponseSuccess({ items: filtered, total: filtered.length });
});
