import { Link, useParams } from 'react-router-dom';
import { useEnrollPath, usePathDetail, useUnenrollPath } from '../api/queries';
import type { PathItemStatus } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { contentHref, formatMinutes } from '../lib/format';

function ItemRow({ item }: { item: PathItemStatus }) {
  return (
    <li>
      <article className={`index-card index-card--${item.kind}`}>
        <p className="index-card__meta">
          {item.status === 'complete' ? '✓ done' : '○ to do'} · {item.kind} ·{' '}
          {formatMinutes(item.estimated_time_minutes)}
        </p>
        <h3 className="index-card__title">
          <Link to={contentHref(item.kind, item.id)}>{item.title}</Link>
        </h3>
      </article>
    </li>
  );
}

export function PathRoute() {
  const { id } = useParams<{ id: string }>();
  const path = usePathDetail(id);
  const enroll = useEnrollPath();
  const unenroll = useUnenrollPath();
  const detail = path.data;

  const nextItem = detail?.next_item_id
    ? detail.units.flatMap((unit) => unit.items).find((item) => item.id === detail.next_item_id)
    : undefined;

  return (
    <div className="stack">
      <PageHeading kicker="Course Rail" title={detail?.title ?? 'Path'} />

      <QueryState
        isLoading={path.isLoading}
        isError={path.isError}
        error={path.error}
        loadingLabel="Unrolling the map…"
      >
        {detail ? (
          <div className="stack">
            <Panel
              title="The route"
              eyebrow={`${detail.path_type === 'career' ? 'Career path' : 'Skill path'} · ~${detail.estimated_hours}h · ${detail.percent_complete}% complete`}
            >
              <p>{detail.description}</p>
              <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
                {nextItem ? (
                  <Link
                    className="command-btn command-btn--pine"
                    to={contentHref(nextItem.kind, nextItem.id)}
                  >
                    Continue: {nextItem.title}
                  </Link>
                ) : (
                  <p className="muted">Path complete. Well walked.</p>
                )}
                {detail.enrolled ? (
                  <button
                    className="command-btn"
                    type="button"
                    disabled={unenroll.isPending}
                    onClick={() => unenroll.mutate(detail.id)}
                  >
                    Unenroll
                  </button>
                ) : (
                  <button
                    className="command-btn"
                    type="button"
                    disabled={enroll.isPending}
                    onClick={() => enroll.mutate(detail.id)}
                  >
                    Enroll
                  </button>
                )}
              </div>
            </Panel>

            {detail.units.map((unit) => (
              <Panel
                key={unit.id}
                title={unit.title}
                eyebrow={`${unit.percent_complete}% · ${unit.items.length} items`}
              >
                <p className="muted">{unit.description}</p>
                <ul className="card-list">
                  {unit.items.map((item) => (
                    <ItemRow key={item.id} item={item} />
                  ))}
                </ul>
              </Panel>
            ))}
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}
