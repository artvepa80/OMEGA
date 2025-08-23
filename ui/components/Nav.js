import Link from 'next/link';

export default function Nav() {
  return (
    <nav className="nav">
      <div className="brand">OMEGA UI</div>
      <div className="links">
        <Link href="/">Dashboard</Link>
        <Link href="/predict">Predictions</Link>
        <Link href="/backtest">Backtests</Link>
        <Link href="/files">Outputs</Link>
        <Link href="/logs">Logs</Link>
        <Link href="/twilio">Twilio</Link>
        <Link href="/scheduler">Scheduler</Link>
      </div>
    </nav>
  );
}


