import { useEffect, useState } from 'react';
import { apiGet } from '../lib/api';

export default function Home() {
  const [status, setStatus] = useState(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    apiGet('/status')
      .then(setStatus)
      .catch(e => setErr(String(e)));
  }, []);

  return (
    <div>
      <h1>🤖 OMEGA Dashboard</h1>
      {err && <p className="error">{err}</p>}
      {!status ? (
        <p>Cargando estado…</p>
      ) : (
        <div className="card">
          <p><b>API OK:</b> {String(status.ok)}</p>
          {status.status && (
            <>
              <p><b>Modo actual:</b> {status.status.current_mode}</p>
              <p><b>Salud:</b> pipeline {status.status.system_health?.pipeline ? '✅' : '❌'} | agentic {status.status.system_health?.agentic ? '✅' : '❌'}</p>
              <p><b>Predicciones totales:</b> {status.status.statistics?.total_predictions}</p>
            </>
          )}
        </div>
      )}
      <div className="grid">
        <a className="card" href="/predict">🎯 Hacer predicción</a>
        <a className="card" href="/backtest">📊 Correr backtest</a>
        <a className="card" href="/files">📁 Ver outputs</a>
        <a className="card" href="/logs">🧾 Logs en vivo</a>
        <a className="card" href="/twilio">📨 Twilio test</a>
        <a className="card" href="/scheduler">🕐 Scheduler</a>
      </div>
    </div>
  );
}


