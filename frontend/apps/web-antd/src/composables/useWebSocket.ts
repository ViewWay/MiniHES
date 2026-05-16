import { ref, onUnmounted } from 'vue';

import { useAccessStore } from '@vben/stores';

interface WSMessage {
  topic: string;
  type: string;
  data: any;
}

const MAX_RETRIES = 3;

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const connected = ref(false);
  const lastMessage = ref<WSMessage | null>(null);
  const subscribers = ref<Map<string, (data: any) => void>>(new Map());
  let retryCount = 0;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (retryCount >= MAX_RETRIES) return;

    const accessStore = useAccessStore();
    const token = accessStore.accessToken;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_GLOB_API_URL?.replace(/^\/\//, '') || 'localhost:8000';
    const wsUrl = `${protocol}//${host.replace(/\/api\/v\d+$/, '')}/ws?token=${token}`;

    try {
      ws.value = new WebSocket(wsUrl);
    } catch {
      return;
    }

    ws.value.onopen = () => {
      retryCount = 0;
      connected.value = true;
    };

    ws.value.onclose = () => {
      connected.value = false;
      retryCount++;
      if (retryCount < MAX_RETRIES) {
        retryTimer = setTimeout(() => connect(), 5000);
      }
    };

    ws.value.onerror = () => {
      ws.value?.close();
    };

    ws.value.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        lastMessage.value = message;
        const callback = subscribers.value.get(message.topic);
        callback?.(message.data);
      } catch {
        /* ignore parse errors */
      }
    };
  }

  function subscribe(topic: string, callback: (data: any) => void) {
    subscribers.value.set(topic, callback);
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ action: 'subscribe', topics: [topic] }));
    }
  }

  function unsubscribe(topic: string) {
    subscribers.value.delete(topic);
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ action: 'unsubscribe', topics: [topic] }));
    }
  }

  function disconnect() {
    if (retryTimer) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    retryCount = MAX_RETRIES;
    ws.value?.close();
    ws.value = null;
    connected.value = false;
  }

  onUnmounted(() => {
    disconnect();
  });

  return { connected, lastMessage, subscribe, unsubscribe, connect, disconnect };
}
