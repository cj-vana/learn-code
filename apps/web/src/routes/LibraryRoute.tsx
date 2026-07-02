import { Link } from 'react-router-dom';
import { useContentList } from '../api/queries';
import type { ContentSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';
import { formatMinutes } from '../lib/format';

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
  const grouped = groupByDifficulty(content.data ?? []);

  return (
    <div className="stack">
      <PageHeading kicker="Pattern Atlas" title="The whole catalogue on one shelf" />

      <QueryState
        isLoading={content.isLoading}
        isError={content.isError}
        error={content.error}
        loadingLabel="Pulling the catalogue…"
      >
        {grouped.length > 0 ? (
          <div className="stack">
            {grouped.map(([difficulty, items]) => (
              <Panel
                key={difficulty}
                title={difficulty}
                eyebrow={`${items.length} exercise${items.length === 1 ? '' : 's'}`}
              >
                <ul className="card-list">
                  {items.map((item) => (
                    <li key={item.id}>
                      <article className="index-card index-card--exercise">
                        <p className="index-card__meta">
                          {item.kind} · {formatMinutes(item.estimated_time_minutes)}
                        </p>
                        <h3 className="index-card__title">
                          <Link to={`/exercise/${encodeURIComponent(item.id)}`}>
                            {item.title}
                          </Link>
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
          <p className="muted">The catalogue is empty.</p>
        )}
      </QueryState>
    </div>
  );
}
