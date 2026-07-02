import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useContentList } from '../api/queries';
import type { ContentSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';
import { contentHref, formatMinutes } from '../lib/format';

const KIND_FILTERS = ['all', 'lesson', 'exercise', 'quiz'] as const;
type KindFilter = (typeof KIND_FILTERS)[number];

function groupByDifficulty(items: ContentSummary[]): [string, ContentSummary[]][] {
  const order = ['intro', 'easy', 'medium', 'hard'];
  const buckets = new Map<string, ContentSummary[]>();
  for (const item of items) {
    const key = item.difficulty || 'unsorted';
    const bucket = buckets.get(key) ?? [];
    bucket.push(item);
    buckets.set(key, bucket);
  }
  return [...buckets.entries()].sort(
    (a, b) => (order.indexOf(a[0]) + 1 || 99) - (order.indexOf(b[0]) + 1 || 99),
  );
}

export function LibraryRoute() {
  const content = useContentList();
  const [kind, setKind] = useState<KindFilter>('all');
  const items = (content.data ?? []).filter((item) => kind === 'all' || item.kind === kind);
  const grouped = groupByDifficulty(items);

  return (
    <div className="stack">
      <PageHeading kicker="Pattern Atlas" title="The whole catalogue on one shelf" />

      <div className="chip-row" role="group" aria-label="Filter by kind">
        {KIND_FILTERS.map((filter) => (
          <button
            key={filter}
            type="button"
            className="command-btn"
            aria-pressed={kind === filter}
            onClick={() => setKind(filter)}
          >
            {filter === 'all' ? 'everything' : `${filter}s`}
          </button>
        ))}
      </div>

      <QueryState
        isLoading={content.isLoading}
        isError={content.isError}
        error={content.error}
        loadingLabel="Pulling the catalogue…"
      >
        {grouped.length > 0 ? (
          <div className="stack">
            {grouped.map(([difficulty, groupItems]) => (
              <Panel
                key={difficulty}
                title={difficulty}
                eyebrow={`${groupItems.length} item${groupItems.length === 1 ? '' : 's'}`}
              >
                <ul className="card-list">
                  {groupItems.map((item) => (
                    <li key={item.id}>
                      <article className={`index-card index-card--${item.kind}`}>
                        <p className="index-card__meta">
                          {item.kind} · {formatMinutes(item.estimated_time_minutes)}
                        </p>
                        <h3 className="index-card__title">
                          <Link to={contentHref(item.kind, item.id)}>{item.title}</Link>
                        </h3>
                        <div className="chip-row" style={{ marginTop: 'var(--space-2)' }}>
                          {item.concepts.map((concept) => (
                            <PatternChip key={concept} pattern={concept} />
                          ))}
                        </div>
                      </article>
                    </li>
                  ))}
                </ul>
              </Panel>
            ))}
          </div>
        ) : (
          <p className="muted">Nothing on this shelf yet.</p>
        )}
      </QueryState>
    </div>
  );
}
