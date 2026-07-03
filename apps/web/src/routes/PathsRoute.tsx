import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useEnrollPath, usePaths } from '../api/queries';
import type { PathLevel, PathSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';

function PathCard({ path }: { path: PathSummary }) {
  const enroll = useEnrollPath();
  return (
    <article className={`index-card index-card--${path.path_type}`}>
      <p className="index-card__meta">
        {path.path_type === 'career' ? 'Career path' : 'Skill path'} · {path.level} ·{' '}
        {path.units} units · ~{path.estimated_hours}h
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
      {path.assumed_concepts.length > 0 ? (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <p className="index-card__meta">Before you start, you should know</p>
          <div className="chip-row">
            {path.assumed_concepts.map((concept) => (
              <span key={concept} className="pattern-chip">
                {concept}
              </span>
            ))}
          </div>
        </div>
      ) : null}
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

const LEVELS: PathLevel[] = ['beginner', 'intermediate', 'advanced'];
const LEVEL_RANK: Record<PathLevel, number> = { beginner: 0, intermediate: 1, advanced: 2 };

export function PathsRoute() {
  const paths = usePaths();
  const [level, setLevel] = useState<PathLevel | 'all'>('all');
  const items = [...(paths.data ?? [])]
    .filter((path) => level === 'all' || path.level === level)
    .sort((a, b) => LEVEL_RANK[a.level] - LEVEL_RANK[b.level]);
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
          <Panel
            title="How much Python do you have?"
            eyebrow="Filter by level — or take the placement check"
            actions={
              <Link className="command-btn" to="/start">
                Not sure? Start Here
              </Link>
            }
          >
            <div className="chip-row">
              <button
                type="button"
                className="pattern-chip"
                aria-pressed={level === 'all'}
                onClick={() => setLevel('all')}
              >
                all levels
              </button>
              {LEVELS.map((choice) => (
                <button
                  key={choice}
                  type="button"
                  className="pattern-chip"
                  aria-pressed={level === choice}
                  onClick={() => setLevel(choice)}
                >
                  {choice}
                </button>
              ))}
            </div>
          </Panel>
          {careers.length > 0 ? (
            <Panel title="Career paths" eyebrow="The long road, end to end">
              <ul className="card-list">
                {careers.map((path) => (
                  <li key={path.id}>
                    <PathCard path={path} />
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
          {skills.length > 0 ? (
            <Panel title="Skill paths" eyebrow="Focused climbs">
              <ul className="card-list">
                {skills.map((path) => (
                  <li key={path.id}>
                    <PathCard path={path} />
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </div>
      </QueryState>
    </div>
  );
}
