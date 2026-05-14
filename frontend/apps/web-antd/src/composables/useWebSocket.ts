import { ref, onUnmounted } from 'vue';
import { useAccessStore } from '@vben/stores';

interface WSMessage {
  topic: string;
  type: string;
  data: any;
}

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const connected = ref(false);
  const lastMessage = ref<WSMessage | null>(null);
  const subscribers = ref<Map<string, (data: any) => void>>(new Map());

  function connect() {
    const accessStore = useAccessStore();
    const token = accessStore.accessToken;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_GLOB_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
    const wsUrl = `${protocol}//${host.replace(/\/api\/v\d+$/, '')}/ws?token=${token}`;

    ws.value = new WebSocket(wsUrl);

    ws.value.onopen = () => {
      connected.value = true;
    };

    ws.value.onclose = () => {
      connected.value = false;
      setTimeout(() => connect(), 5000);
    };

    ws.value.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        lastMessage.value = message;
        const callback = subscribers.value.get(message.topic);
        callback?.(message.data);
      } catch { /* ignore parse errors */ }
    };
  }

  function subscribe(topic: string, callback: (data: any) => void) {
    subscribers.value.set(topic, callback);
    ws.value?.send(JSON.stringify({ action: 'subscribe', topics: [topic] }));
  }

  function unsubscribe(topic: string) {
    subscribers.value.delete(topic);
    ws.value?.send(JSON.stringify({ action: 'unsubscribe', topics: [topic] }));
  }

  function disconnect() {
    ws.value?.close();
    ws.value = null;
    connected.value = false;
  }

  onUnmounted(() => {
    disconnect();
  });

  return { connected, lastMessage, subscribe, unsubscribe, connect, disconnect };
}
