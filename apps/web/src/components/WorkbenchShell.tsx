import { NavLink, Outlet } from 'react-router-dom';
import { RuntimeStatusStrip } from './RuntimeStatusStrip';

const NAV = [
  { to: '/learn', label: "Today's Bench" },
  { to: '/playground', label: 'Scratch Bench' },
  { to: '/review', label: 'Mistake Lab' },
  { to: '/library', label: 'Pattern Atlas' },
  { to: '/progress', label: 'Evidence Ledger' },
];

/** The workshop frame every route lives inside: masthead, the tools rail,
 *  runtime instrument strip, the work surface, and the ledger footer. */
export function WorkbenchShell() {
  return (
    <div className="shell">
      <header className="shell__masthead">
        <div>
          <p className="shell__brand">
            Workbench<span>·</span>Ledger
          </p>
          <p className="shell__tagline">a study workshop for interview python</p>
        </div>
        <p className="shell__tagline">bench notes · evidence · repetition</p>
      </header>

      <nav className="shell__nav" aria-label="Primary">
        {NAV.map((item) => (
          <NavLink key={item.to} to={item.to}>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <RuntimeStatusStrip />

      <main className="shell__main">
        <Outlet />
      </main>

      <footer className="shell__foot">
        Workbench Ledger — every attempt is filed as evidence.
      </footer>
    </div>
  );
}
