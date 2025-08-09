import { useState } from 'react';
import { apiPost } from '../lib/api';

export default function TwilioPage() {
  const [to, setTo] = useState('');
  const [body, setBody] = useState('Hola desde OMEGA 👋');
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function send(e) {
    e.preventDefault();
    setErr(''); setResp(null); setLoading(true);
    try {
      const r = await apiPost('/ui/integrations/twilio/test', { to, body });
      setResp(r);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>📨 Twilio Test</h1>
      <form onSubmit={send} className="form">
        <label>Destino (opcional, si vacío usa TWILIO_TO_NUMBER)</label>
        <input value={to} onChange={e => setTo(e.target.value)} placeholder="+51999999999" />
        <label>Mensaje</label>
        <input value={body} onChange={e => setBody(e.target.value)} />
        <button type="submit" disabled={loading}>{loading ? 'Enviando…' : 'Enviar'}</button>
      </form>
      {err && <p className="error">{err}</p>}
      {resp && (
        <div className="card">
          <p><b>SID:</b> {resp.sid}</p>
          <p><b>Status:</b> {resp.status}</p>
          <p>Revisa tu teléfono 😉</p>
        </div>
      )}
    </div>
  );
}


