import { computed, watch } from 'vue';

import { usePreferences } from '@vben/preferences';

export function useChartTheme() {
  const { isDark } = usePreferences();

  const chartColors = computed(() => {
    const dark = isDark.value;
    return {
      text: dark ? '#d1d5db' : '#374151',
      textSecondary: dark ? '#9ca3af' : '#6b7280',
      axisLine: dark ? '#374151' : '#e5e7eb',
      splitLine: dark ? '#1f2937' : '#f3f4f6',
      tooltipBg: dark ? '#1f2937' : '#ffffff',
      tooltipBorder: dark ? '#374151' : '#e5e7eb',
      tooltipText: dark ? '#f3f4f6' : '#111827',
    };
  });

  function themedAxis(
    direction: 'x' | 'y',
    overrides: Record<string, any> = {},
  ) {
    const c = chartColors.value;
    const base = {
      axisLabel: { color: c.text },
      axisLine: { lineStyle: { color: c.axisLine } },
      axisTick: { lineStyle: { color: c.axisLine } },
      nameTextStyle: { color: c.textSecondary },
      splitLine: {
        lineStyle: {
          color: direction === 'y' ? c.splitLine : 'transparent',
        },
      },
    };
    return { ...base, ...overrides };
  }

  function themedTooltip(overrides: Record<string, any> = {}) {
    const c = chartColors.value;
    return {
      trigger: 'axis' as const,
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      ...overrides,
    };
  }

  function themedLegend(overrides: Record<string, any> = {}) {
    const c = chartColors.value;
    return {
      textStyle: { color: c.text },
      ...overrides,
    };
  }

  function themedGauge(
    overrides: Record<string, any> = {},
  ) {
    const c = chartColors.value;
    return {
      axisTick: { distance: -16, lineStyle: { color: c.textSecondary, width: 1 } },
      splitLine: { distance: -16, lineStyle: { color: c.textSecondary, width: 2 } },
      axisLabel: { distance: 22, color: c.textSecondary, fontSize: 10 },
      detail: { color: c.text },
      title: { color: c.textSecondary, fontSize: 12 },
      ...overrides,
    };
  }

  function watchThemeAndRerender(renderFn: () => void, immediate = false) {
    watch(isDark, () => {
      renderFn();
    }, { immediate });
  }

  return { chartColors, isDark, themedAxis, themedGauge, themedLegend, themedTooltip, watchThemeAndRerender };
}
