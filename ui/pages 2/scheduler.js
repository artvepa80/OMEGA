import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../lib/api';

const DAY_OPTS = [
  { key: 'tue', label: 'Martes' },
  { key: 'thu', label: 'Jueves' },
  { key: 'sat', label: 'Sábado' },
];

export default function Scheduler() {
  const [cfg, setCfg] = useState({
    days: ['tue','thu','sat'],
    time: '20:30',
    tz: 'America/Lima',
    playlist_url: '',
    notify_twilio: true
  });
  const [nextRuns, setNextRuns] = useState([]);
  const [err, setErr] = useState('');
  const [saving, setSaving] = useState(false);
  const [firing, setFiring] = useState(false);
  const [reloading, setReloading] = useState(false);

  async function load() {
    setErr('');
    try {
      const r = await apiGet('/ui/scheduler');
      setCfg(r.config);
      setNextRuns(r.next_runs || []);
    } catch (e) {
      setErr(String(e));
    }
  }

  useEffect(() => { load(); }, []);

  function toggleDay(key) {
    setCfg(s => {
      const set = new Set(s.days || []);
      if (set.has(key)) set.delete(key); else set.add(key);
      return { ...s, days: Array.from(set) };
    });
  }

  async function save() {
    setSaving(true); setErr('');
    try {
      const r = await apiPost('/ui/scheduler', cfg);
      setCfg(r.config);
      setNextRuns(r.next_runs || []);
    } catch (e) {
      setErr(String(e));
    } finally {
      setSaving(false);
    }
  }

  async function reloadSched() {
    setReloading(true); setErr('');
    try {
      const r = await apiPost('/ui/scheduler/reload', {});
      setCfg(r.config);
      setNextRuns(r.next_runs || []);
    } catch (e) {
      setErr(String(e));
    } finally {
      setReloading(false);
    }
  }

  async function fireNow() {
    setFiring(true); setErr('');
    try {
      const r = await apiPost('/ui/scheduler/fire-now', {});
      alert(`Disparo manual OK (prediction_id=${r.result_id || 'n/a'})`);
    } catch (e) {
      setErr(String(e));
    } finally {
      setFiring(false);
    }
  }

  return (
    <div>
      <h1>🕐 Scheduler</h1>
      {err && <p className="error">{err}</p>}
      <div className="card">
        <div className="form">
          <label>Días (Lima)</label>
          <div style={{display:'flex', gap:10}}>
            {DAY_OPTS.map(d => (
              <label key={d.key} style={{display:'flex', gap:6, alignItems:'center'}}>
                <input type="checkbox"
                       checked={(cfg.days || []).includes(d.key)}
                       onChange={()=>toggleDay(d.key)} />
                {d.label}
              </label>
            ))}
          </div>

          <label>Hora (24h)</label>
          <input type="time" value={cfg.time} onChange={e=>setCfg(s=>({...s, time:e.target.value}))} />

          <label>Zona horaria</label>
          <input value={cfg.tz} onChange={e=>setCfg(s=>({...s, tz:e.target.value}))} placeholder="America/Lima" />

          <label>YouTube Playlist (opcional)</label>
          <input value={cfg.playlist_url || ''} onChange={e=>setCfg(s=>({...s, playlist_url:e.target.value}))}
                 placeholder="https://youtube.com/playlist?list=..." />

          <label>Notificar por Twilio (si está configurado)</label>
          <select value={cfg.notify_twilio ? '1':'0'} onChange={e=>setCfg(s=>({...s, notify_twilio: e.target.value==='1'}))}>
            <option value="1">Sí</option>
            <option value="0">No</option>
          </select>

          <div style={{display:'flex', gap:8, marginTop:10}}>
            <button onClick={save} disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
            <button onClick={reloadSched} disabled={reloading}>{reloading ? 'Reiniciando…' : 'Recargar scheduler'}</button>
            <button onClick={fireNow} disabled={firing}>{firing ? 'Disparando…' : 'Disparar ahora'}</button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Próximas ejecuciones</h3>
        {!nextRuns.length ? <p>Sin próximas ejecuciones (revisa la configuración).</p> : (
          <ul>{nextRuns.map((t,i)=><li key={i}><code>{t}</code></li>)}</ul>
        )}
      </div>
    </div>
  );
}


