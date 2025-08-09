import { useEffect, useRef, useState } from 'react';
import { logsWebSocketURL } from '../lib/api';

export default function Logs() {
  const [lines, setLines] = useState([]);
  const [connected, setConnected] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const url = logsWebSocketURL();
    const ws = new WebSocket(url);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (evt) => {
      setLines(prev => {
        const next = [...prev, evt.data];
        return next.slice(-500);
      });
      if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      <h1>🧾 Logs en vivo {connected ? '🟢' : '⚪'}</h1>
      <div className="logbox" ref={ref}>
        {lines.map((l,i) => <div key={i} className="logline">{l}</div>)}
      </div>
    </div>
  );
}


