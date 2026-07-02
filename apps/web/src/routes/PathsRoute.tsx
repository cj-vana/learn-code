import { Link } from 'react-router-dom';
import { useEnrollPath, usePaths } from '../api/queries';
import type { PathSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';

function PathCard({ path }: { path: PathSummary }) {
  const enroll = useEnrollPath();
  return (
    <article className={`index-card index-card--${path.path_type}`}>
      <p className="index-card__meta">
        {path.path_type === 'career' ? 'Career path' : 'Skill path'} · {path.units} units ·{' '}
        ~{path.estimated_hours}h
      </p>
      <h3 className="index-card__title">
        <Link to={`/path/${encodeURIComponent(path.id)}`}>{path.title}</Link>
      </h3>
      <p>{path.description}</p>
      <ul className="mistake-inbox">
        {path.outcomes.map((outcome) => (
          <li key={outcome}>{outcome}</li>
        ))}
      </ul>
      <p className="index-card__meta">{path.percent_complete}% complete</p>
      <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
        {path.enrolled ? (
          <Link className="command-btn command-btn--pine" to={`/path/${encodeURIComponent(path.id)}`}>
            Continue
          </Link>
        ) : (
          <button
            className="command-btn command-btn--pine"
            type="button"
            disabled={enroll.isPending}
            onClick={() => enroll.mutate(path.id)}
          >
            Enroll
          </button>
        )}
      </div>
    </article>
  );
}

export function PathsRoute() {
  const paths = usePaths();
  const items = paths.data ?? [];
  const careers = items.filter((path) => path.path_type === 'career');
  const skills = items.filter((path) => path.path_type === 'skill');

  return (
    <div className="stack">
      <PageHeading kicker="Course Rail" title="Pick a path and follow it" />

      <QueryState
        isLoading={paths.isLoading}
        isError={paths.isError}
        error={paths.error}
        loadingLabel="Unrolling the maps…"
      >
        <div className="stack">
          <Panel title="Career paths" eyebrow="The long road, end to end">
            <ul className="card-list">
              {careers.map((path) => (
                <li key={path.id}>
                  <PathCard path={path} />
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Skill paths" eyebrow="Focused climbs">
            <ul className="card-list">
              {skills.map((path) => (
                <li key={path.id}>
                  <PathCard path={path} />
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </QueryState>
    </div>
  );
}
