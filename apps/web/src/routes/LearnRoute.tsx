import { Link } from 'react-router-dom';
import { usePlan, useProgress } from '../api/queries';
import type { PlanItem } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';
import { RationaleDisclosure } from '../components/RationaleDisclosure';
import { contentHref, formatMinutes, humanizeConcept } from '../lib/format';

function planHref(item: PlanItem): string {
  return contentHref(item.kind, item.content_id);
}

function AdaptivePlanCard({ item }: { item: PlanItem }) {
  return (
    <article className={`index-card index-card--${item.kind}`}>
      <p className="index-card__meta">
        Next up · {item.kind} · {formatMinutes(item.estimated_time_minutes)}
      </p>
      <h3 className="index-card__title">{item.title}</h3>
      <div className="chip-row" style={{ margin: 'var(--space-2) 0' }}>
        {item.concepts.map((concept) => (
          <PatternChip key={concept} pattern={concept} />
        ))}
      </div>
      <RationaleDisclosure rationale={item.rationale} />
      <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
        <Link className="command-btn command-btn--pine" to={planHref(item)}>
          Open the bench
        </Link>
      </div>
    </article>
  );
}

function SessionStack({ items }: { items: PlanItem[] }) {
  if (items.length === 0) {
    return <p className="muted">Nothing else queued. The bench is clear.</p>;
  }
  return (
    <ul className="card-list">
      {items.map((item) => (
        <li key={item.id}>
          <article className={`index-card index-card--${item.kind}`}>
            <p className="index-card__meta">
              {item.kind} · {formatMinutes(item.estimated_time_minutes)} · priority{' '}
              {item.priority.toFixed(2)}
            </p>
            <h3 className="index-card__title">
              <Link to={planHref(item)}>{item.title}</Link>
            </h3>
            <p className="index-card__rationale">{item.rationale.reason}</p>
          </article>
        </li>
      ))}
    </ul>
  );
}

export function LearnRoute() {
  const plan = usePlan();
  const progress = useProgress();

  const items = plan.data ?? [];
  const [lead, ...rest] = items;
  const patternMap = Array.from(new Set(items.flatMap((item) => item.concepts)));

  return (
    <div className="stack">
      <PageHeading kicker="Today's Workbench" title="Set out the day's work" />

      <div className="page-grid">
        <div className="stack">
          <Panel title="Adaptive plan" eyebrow="Top of the queue">
            <QueryState
              isLoading={plan.isLoading}
              isError={plan.isError}
              error={plan.error}
              loadingLabel="Reading today's plan…"
            >
              {lead ? (
                <AdaptivePlanCard item={lead} />
              ) : (
                <p className="muted">No plan items yet. Seed some progress to begin.</p>
              )}
            </QueryState>
          </Panel>

          <Panel title="Session stack" eyebrow="The rest of the bench">
            <QueryState
              isLoading={plan.isLoading}
              isError={plan.isError}
              error={plan.error}
            >
              <SessionStack items={rest} />
            </QueryState>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Pattern map" eyebrow="What today touches">
            <QueryState
              isLoading={plan.isLoading}
              isError={plan.isError}
              error={plan.error}
            >
              {patternMap.length > 0 ? (
                <div className="chip-row">
                  {patternMap.map((concept) => (
                    <PatternChip key={concept} pattern={concept} />
                  ))}
                </div>
              ) : (
                <p className="muted">No patterns queued.</p>
              )}
            </QueryState>
          </Panel>

          <Panel title="Mistake inbox" eyebrow="Filed for follow-up" tone="ink">
            <QueryState
              isLoading={progress.isLoading}
              isError={progress.isError}
              error={progress.error}
              loadingLabel="Opening the inbox…"
            >
              {progress.data && progress.data.recent_mistakes.length > 0 ? (
                <ul className="mistake-inbox">
                  {progress.data.recent_mistakes.map((mistake, index) => (
                    <li key={index}>{humanizeConcept(mistake)}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Inbox clear — no recent mistakes on file.</p>
              )}
            </QueryState>
          </Panel>
        </div>
      </div>
    </div>
  );
}
