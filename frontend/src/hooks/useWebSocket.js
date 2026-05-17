import { useState, useEffect, useRef } from 'react';

export function useWebSocket(url) {
  const [data, setData] = useState([]);
  const [globalData, setGlobalData] = useState(null);
  const [status, setStatus] = useState('Connecting...');
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setStatus('Connected');
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'update') {
        setData(message.data);
        if (message.global) {
          setGlobalData(message.global);
        }
      }
    };

    ws.current.onerror = (error) => {
      setStatus('Error');
      console.error('WebSocket Error:', error);
    };

    ws.current.onclose = () => {
      setStatus('Disconnected');
      // In production, add reconnect logic here
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  return { data, globalData, status };
}
