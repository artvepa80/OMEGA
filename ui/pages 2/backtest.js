import { useState } from 'react';
import { apiPost } from '../lib/api';

export default function Backtest() {
  const [form, setForm] = useState({
    data: 'data/historial_kabala_github_fixed.csv',
    models: 'consensus,transformer_deep,lstm_v2,genetico,montecarlo,apriori',
    windows: 'rolling_200',
    top_n: 10,
    seed: 42,
    out: 'results/accuracy_analysis/run_ui'
  });
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  function upd(k, v) { setForm(s => ({...s, [k]: v})); }

  async function submit(e) {
    e.preventDefault();
    setErr(''); setResp(null); setLoading(true);
    try {
      const r = await apiPost('/ui/eval/backtest', form);
      setResp(r);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>📊 Backtest</h1>
      <form onSubmit={submit} className="form grid2">
        <label>data</label>
        <input value={form.data} onChange={e=>upd('data', e.target.value)} />
        <label>models</label>
        <input value={form.models} onChange={e=>upd('models', e.target.value)} />
        <label>windows</label>
        <input value={form.windows} onChange={e=>upd('windows', e.target.value)} />
        <label>top_n</label>
        <input type="number" value={form.top_n} onChange={e=>upd('top_n', Number(e.target.value))} />
        <label>seed</label>
        <input type="number" value={form.seed} onChange={e=>upd('seed', Number(e.target.value))} />
        <label>out</label>
        <input value={form.out} onChange={e=>upd('out', e.target.value)} />
        <button type="submit" disabled={loading} style={{gridColumn:'1 / span 2'}}>
          {loading ? 'Lanzando…' : 'Ejecutar backtest'}
        </button>
      </form>
      {err && <p className="error">{err}</p>}
      {resp && (
        <div className="card">
          <p><b>Status:</b> {resp.status}</p>
          <p><b>CMD:</b> <code>{resp.cmd}</code></p>
          <p><b>Out:</b> {resp.out}</p>
          <p>Revisa luego en <code>{resp.out}</code> → carpeta con <i>report.html</i> y <i>plots/</i></p>
        </div>
      )}
    </div>
  );
}


