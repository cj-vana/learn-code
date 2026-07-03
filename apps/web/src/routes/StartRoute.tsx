import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { usePaths } from '../api/queries';
import type { PathSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { conceptChoices, place } from '../lib/placement';

function PathLine({ path }: { path: PathSummary }) {
  return (
    <li>
      <article className={`index-card index-card--${path.path_type}`}>
        <p className="index-card__meta">
          {path.path_type === 'career' ? 'Career path' : 'Skill path'} · {path.units} units · ~
          {path.estimated_hours}h
        </p>
        <h3 className="index-card__title">
          <Link to={`/path/${encodeURIComponent(path.id)}`}>{path.title}</Link>
        </h3>
        <p>{path.description}</p>
      </article>
    </li>
  );
}

export function StartRoute() {
  const paths = usePaths();
  const [known, setKnown] = useState<Set<string>>(new Set());

  const summaries = paths.data ?? [];
  const choices = useMemo(() => conceptChoices(summaries), [summaries]);
  const placement = useMemo(() => place(summaries, known), [summaries, known]);
  const [first, ...alsoReady] = placement.ready;

  const toggle = (concept: string) => {
    setKnown((prev) => {
      const next = new Set(prev);
      if (next.has(concept)) {
        next.delete(concept);
      } else {
        next.add(concept);
      }
      return next;
    });
  };

  return (
    <div className="stack">
      <PageHeading kicker="Placement" title="Where should I start?" />

      <QueryState
        isLoading={paths.isLoading}
        isError={paths.isError}
        error={paths.error}
        loadingLabel="Laying out the map…"
      >
        <div className="stack">
          <Panel
            title="What do you already know?"
            eyebrow="Tick everything you could use in a small program today"
          >
            <p className="muted">
              Never written code before? Leave everything unticked — that is a perfectly good
              answer, and the recommendation below already points at the right first step.
            </p>
            <div className="chip-row" style={{ marginTop: 'var(--space-3)' }}>
              <button
                type="button"
                className="pattern-chip"
                aria-pressed={known.size === 0}
                onClick={() => setKnown(new Set())}
              >
                I'm brand new
              </button>
              {choices.map((concept) => (
                <button
                  key={concept}
                  type="button"
                  className="pattern-chip"
                  aria-pressed={known.has(concept)}
                  onClick={() => toggle(concept)}
                >
                  {concept}
                </button>
              ))}
            </div>
          </Panel>

          {first ? (
            <Panel title="Start here" eyebrow="The most advanced path you're ready for today">
              <ul className="card-list">
                <PathLine path={first} />
              </ul>
            </Panel>
          ) : null}

          {alsoReady.length > 0 ? (
            <Panel title="Also ready for you" eyebrow={`${alsoReady.length} more you could start now`}>
              <ul className="card-list">
                {alsoReady.map((path) => (
                  <PathLine key={path.id} path={path} />
                ))}
              </ul>
            </Panel>
          ) : null}

          {placement.stretch.length > 0 ? (
            <Panel
              title="Almost within reach"
              eyebrow="One or two concepts short — the gaps are listed"
            >
              <ul className="card-list">
                {placement.stretch.map(({ path, missing }) => (
                  <li key={path.id}>
                    <article className={`index-card index-card--${path.path_type}`}>
                      <h3 className="index-card__title">
                        <Link to={`/path/${encodeURIComponent(path.id)}`}>{path.title}</Link>
                      </h3>
                      <p className="index-card__meta">You'd want to pick up</p>
                      <div className="chip-row">
                        {missing.map((concept) => (
                          <span key={concept} className="pattern-chip">
                            {concept}
                          </span>
                        ))}
                      </div>
                    </article>
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
