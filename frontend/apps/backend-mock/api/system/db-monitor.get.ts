import { useResponseSuccess } from '~/utils/response';

export default defineEventHandler(() => {
  return useResponseSuccess({
    postgresql: {
      status: 'running',
      version: '16.2',
      database_size: '2.3 GB',
      active_connections: 12,
      max_connections: 100,
      tables_count: 28,
      slow_queries: 2,
      uptime: '45天12小时',
    },
    redis: {
      status: 'running',
      version: '7.2.4',
      used_memory: '256 MB',
      max_memory: '2 GB',
      connected_clients: 8,
      keyspace_hits: 15420,
      keyspace_misses: 230,
      hit_rate: '98.5%',
      uptime: '45天12小时',
    },
    influxdb: {
      status: 'running',
      version: '2.7.5',
      bucket_count: 3,
      total_series: 12500,
      write_points_per_second: 150,
      query_latency_avg: '12ms',
      disk_usage: '8.5 GB',
      retention_policy: '30d',
    },
    last_updated: new Date().toISOString().replace('T', ' ').slice(0, 19),
  });
});
