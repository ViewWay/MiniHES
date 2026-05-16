import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess([
    { id: 1, name: '正向有功总电能', code: '1.0.0.0.0.255', unit: 'kWh', protocol: 'DLMS', description: '累积正向有功电能' },
    { id: 2, name: '当前需量', code: '1.0.1.8.0.255', unit: 'kW', protocol: 'DLMS', description: '当前15分钟需量' },
    { id: 3, name: 'A相电压', code: '1.0.12.7.0.255', unit: 'V', protocol: 'DLMS', description: '相位A电压有效值' },
    { id: 4, name: 'A相电流', code: '1.0.21.7.0.255', unit: 'A', protocol: 'DLMS', description: '相位A电流有效值' },
    { id: 5, name: 'B相电压', code: '1.0.32.7.0.255', unit: 'V', protocol: 'DLMS', description: '相位B电压有效值' },
    { id: 6, name: 'B相电流', code: '1.0.41.7.0.255', unit: 'A', protocol: 'DLMS', description: '相位B电流有效值' },
    { id: 7, name: '电表状态', code: '0.0.1.0.0.255', unit: '', protocol: 'DLMS', description: '电表运行状态字' },
    { id: 8, name: '频率', code: '1.0.14.7.0.255', unit: 'Hz', protocol: 'DLMS', description: '电网频率' },
    { id: 9, name: '功率因数', code: '1.0.13.7.0.255', unit: '', protocol: 'DLMS', description: '总功率因数' },
    { id: 10, name: '正向有功电能（费率1）', code: '1.0.1.8.1.255', unit: 'kWh', protocol: 'DLMS', description: '尖时段电能' },
  ]);
});
