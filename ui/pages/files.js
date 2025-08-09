import { useState, useEffect } from 'react';
import { apiGet } from '../lib/api';

export default function Files() {
  const [ext, setExt] = useState('');
  const [data, setData] = useState({ files: [] });
  const [err, setErr] = useState('');

  async function load() {
    setErr('');
    try {
      const q = ext ? `?ext=${encodeURIComponent(ext)}` : '';
      const r = await apiGet(`/ui/outputs/list${q}`);
      setData(r);
    } catch (e) {
      setErr(String(e));
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h1>📁 Outputs</h1>
      <div className="form">
        <label>Filtrar por extensión (opcional, ej: html / csv / json)</label>
        <input value={ext} onChange={e => setExt(e.target.value)} placeholder="html" />
        <button onClick={load}>Refrescar</button>
      </div>
      {err && <p className="error">{err}</p>}
      <div className="card">
        {!data.files?.length ? <p>Sin archivos</p> : (
          <ul>
            {data.files.map((p, i) => <li key={i}><code>{p}</code></li>)}
          </ul>
        )}
      </div>
      <p style={{marginTop:10}}>Tip: abre los reportes HTML desde tu sistema de archivos local.</p>
    </div>
  );
}


