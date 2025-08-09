import { useState } from 'react';
import { apiPost } from '../lib/api';

export default function Predict() {
  const [mode, setMode] = useState('hybrid');
  const [res, setRes] = useState(null);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function handlePredict(e) {
    e.preventDefault();
    setLoading(true); setErr(''); setRes(null);
    try {
      const r = await apiPost('/ui/predict', { mode });
      setRes(r);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>🎯 Predicción</h1>
      <form onSubmit={handlePredict} className="form">
        <label>Mode</label>
        <select value={mode} onChange={e => setMode(e.target.value)}>
          <option value="pipeline">pipeline</option>
          <option value="agentic">agentic</option>
          <option value="hybrid">hybrid</option>
          <option value="adaptive">adaptive</option>
        </select>
        <button type="submit" disabled={loading}>{loading ? 'Generando…' : 'Predecir'}</button>
      </form>

      {err && <p className="error">{err}</p>}
      {res && (
        <div className="card">
          <p><b>ID:</b> {res.prediction_id}</p>
          <p><b>Modo:</b> {res.mode_used}</p>
          <p><b>Éxito:</b> {String(res.success)}</p>
          <h3>Combinaciones</h3>
          {res.combinations?.length ? (
            <ul>
              {res.combinations.map((c, i) => (
                <li key={i}>
                  <code>{(c.numbers || []).join('-')}</code> · src:<i>{c.source}</i> · conf: <b>{((c.confidence||0)*100).toFixed(1)}%</b>
                </li>
              ))}
            </ul>
          ) : <p>Sin combinaciones</p>}
          {res.exports && (
            <>
              <h3>Exports</h3>
              <pre>{JSON.stringify(res.exports, null, 2)}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}


