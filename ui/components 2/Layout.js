import Nav from './Nav';

export default function Layout({ children }) {
  return (
    <div className="app">
      <Nav />
      <main className="container">{children}</main>
    </div>
  );
}


