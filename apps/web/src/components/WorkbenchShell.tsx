import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { RuntimeStatusStrip } from './RuntimeStatusStrip';
import { useProgress } from '../api/queries';

type IconName = 'home' | 'tree' | 'bolt' | 'refresh' | 'grid' | 'trophy' | 'code' | 'flag';

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, string> = {
    home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/>',
    tree: '<circle cx="12" cy="5" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="18" r="2.4"/><path d="M12 7.4v3.6M12 11l-6 4.6M12 11l6 4.6"/>',
    bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    refresh:
      '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    trophy:
      '<path d="M7 4h10v4a5 5 0 0 1-10 0z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3M9 15h6M10 15v4M14 15v4M8 21h8"/>',
    code: '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13 5l-2 14"/>',
    flag: '<path d="M5 21V4"/><path d="M5 4h13l-2.5 4L18 12H5"/>',
  };
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.1}
      strokeLinecap="round"
      strokeLinejoin="round"
      dangerouslySetInnerHTML={{ __html: paths[name] }}
    />
  );
}

const NAV: { to: string; label: string; icon: IconName; crumb: string }[] = [
  { to: '/learn', label: 'Home', icon: 'home', crumb: 'Your desk' },
  { to: '/start', label: 'Start Here', icon: 'flag', crumb: 'Placement' },
  { to: '/paths', label: 'Skill Tree', icon: 'tree', crumb: 'Python · skill tree' },
  { to: '/timed', label: 'Challenge', icon: 'bolt', crumb: 'Boss bench' },
  { to: '/review', label: 'Review Pile', icon: 'refresh', crumb: 'Spaced review' },
  { to: '/playground', label: 'Scratch', icon: 'code', crumb: 'Scratch bench' },
  { to: '/library', label: 'Pattern Atlas', icon: 'grid', crumb: 'Pattern atlas' },
  { to: '/progress', label: 'Trophy Room', icon: 'trophy', crumb: 'Your evidence' },
];

const XP_PER_LEVEL = 300;
const RING_CIRC = 100.5; // 2πr, r = 16

export function WorkbenchShell() {
  const { pathname } = useLocation();
  const progress = useProgress();
  const summary = progress.data;

  const streak = summary?.streak_days ?? 0;
  const xp = summary
    ? Math.round(summary.concepts.reduce((sum, c) => sum + (c.mastery ?? 0), 0))
    : 0;
  const level = Math.floor(xp / XP_PER_LEVEL) + 1;
  const intoLevel = xp % XP_PER_LEVEL;
  const levelPct = intoLevel / XP_PER_LEVEL;
  const ringOffset = RING_CIRC * (1 - levelPct);
  const toNext = XP_PER_LEVEL - intoLevel;

  const active = NAV.find(
    (n) => pathname === n.to || pathname.startsWith(n.to + '/'),
  );
  // Route-family crumb + section title for detail pages the nav doesn't list.
  const detail: Record<string, [string, string]> = {
    '/exercise': ['Solve bench', 'Quest'],
    '/lesson': ['Lesson', 'Lesson'],
    '/quiz': ['Quick check', 'Quiz'],
    '/path/': ['Skill tree', 'Path'],
  };
  const detailKey = Object.keys(detail).find((k) => pathname.startsWith(k));
  const crumb = active ? active.crumb : detailKey ? detail[detailKey][0] : 'Learn Code';
  const title = active ? active.label : detailKey ? detail[detailKey][1] : 'Learn Code';

  return (
    <div className="cq-shell">
      <aside className="cq-sidebar">
        <NavLink to="/learn" className="cq-brand">
          <span className="cq-logo">&lt;/&gt;</span>
          <span>
            <span className="cq-brand__name">Learn Code</span>
            <span className="cq-brand__tag">learn python by playing</span>
          </span>
        </NavLink>

        <nav className="cq-nav" aria-label="Primary">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} className="cq-nav-btn">
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.to === '/review' && summary && summary.concepts.length > 0 ? null : null}
            </NavLink>
          ))}
        </nav>

        <div className="cq-goal">
          <div className="cq-goal__head">
            <span>Level {level}</span>
            <span>{Math.round(levelPct * 100)}%</span>
          </div>
          <div className="cq-goal__track">
            <div className="cq-goal__fill" style={{ width: `${levelPct * 100}%` }} />
          </div>
          <div className="cq-goal__note">{toNext} XP to level {level + 1}</div>
        </div>
      </aside>

      <div className="cq-main-col">
        <header className="cq-topbar">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="cq-topbar__crumb">{crumb}</div>
            <div className="cq-topbar__title">{title}</div>
          </div>
          <div className="cq-stats">
            <div className="cq-chip cq-chip--streak" title="Day streak">
              <span className="cq-flame">🔥</span>
              {streak}
              <small>day</small>
            </div>
            <div className="cq-chip cq-chip--xp" title="Experience from mastery">
              <span className="cq-gem" />
              {xp.toLocaleString()}
              <small>XP</small>
            </div>
            <div className="cq-level" title={`Level ${level}`}>
              <div className="cq-level__ring">
                <svg width="38" height="38" viewBox="0 0 38 38">
                  <circle
                    cx="19"
                    cy="19"
                    r="16"
                    fill="none"
                    stroke="rgba(255,255,255,.14)"
                    strokeWidth="4"
                  />
                  <circle
                    cx="19"
                    cy="19"
                    r="16"
                    fill="none"
                    stroke="#B9EE3A"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={RING_CIRC}
                    strokeDashoffset={ringOffset}
                  />
                </svg>
                <div className="cq-level__num">{level}</div>
              </div>
              <div>
                <div className="cq-level__name">You</div>
                <div className="cq-level__sub">Level {level}</div>
              </div>
            </div>
          </div>
        </header>

        <RuntimeStatusStrip />

        <main className="shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
