import { useProgress } from '../api/queries';
import type { ConceptSummary } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { MasteryMeter } from '../components/MasteryMeter';
import { formatDueDate, humanizeConcept } from '../lib/format';

function dueRank(concept: ConceptSummary): number {
  if (!concept.review_due_at) return Number.POSITIVE_INFINITY;
  const time = new Date(concept.review_due_at).getTime();
  return Number.isNaN(time) ? Number.POSITIVE_INFINITY : time;
}

export function ReviewRoute() {
  const progress = useProgress();
  const concepts = progress.data?.concepts ?? [];
  const deck = concepts
    .filter((concept) => concept.review_due_at !== null)
    .sort((a, b) => dueRank(a) - dueRank(b));
  const mistakes = progress.data?.recent_mistakes ?? [];

  return (
    <div className="stack">
      <PageHeading kicker="Mistake Lab" title="Work the errors back down" />

      <div className="page-grid">
        <Panel title="Review deck" eyebrow="Concepts coming due">
          <QueryState
            isLoading={progress.isLoading}
            isError={progress.isError}
            error={progress.error}
            loadingLabel="Shuffling the deck…"
          >
            {deck.length > 0 ? (
              <ul className="card-list">
                {deck.map((concept) => (
                  <li key={concept.id}>
                    <article className="index-card index-card--review">
                      <p className="index-card__meta">
                        due {formatDueDate(concept.review_due_at)}
                      </p>
                      <MasteryMeter
                        concept={concept.id}
                        mastery={concept.mastery}
                        label={concept.label}
                      />
                    </article>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Nothing scheduled for review. The deck is empty.</p>
            )}
          </QueryState>
        </Panel>

        <Panel title="Mistake lab" eyebrow="Recent slips to redo" tone="ink">
          <QueryState
            isLoading={progress.isLoading}
            isError={progress.isError}
            error={progress.error}
          >
            {mistakes.length > 0 ? (
              <ul className="mistake-inbox">
                {mistakes.map((mistake, index) => (
                  <li key={index}>{humanizeConcept(mistake)}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">No recent mistakes. Keep the streak going.</p>
            )}
          </QueryState>
        </Panel>
      </div>
    </div>
  );
}
