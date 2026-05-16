import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
  const voltageA = Array.from({ length: 24 }, () => (220 + Math.random() * 5 - 2.5).toFixed(1));
  const currentA = Array.from({ length: 24 }, () => (5 + Math.random() * 3).toFixed(2));
  const activePower = Array.from({ length: 24 }, () => (1.1 + Math.random() * 0.8).toFixed(2));
  const energy = Array.from({ length: 24 }, (_, i) => ((i + 1) * 0.15).toFixed(2));

  return useResponseSuccess({
    meter_id: 1,
    meter_name: '三相表#1',
    date: new Date().toISOString().slice(0, 10),
    hours,
    voltage_a: voltageA,
    current_a: currentA,
    active_power: activePower,
    energy,
    total_energy: '3.48',
    max_demand: '1.89',
    power_factor: '0.98',
  });
});
