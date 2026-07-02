import { useProgress } from '../api/queries';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { MasteryMeter } from '../components/MasteryMeter';
import { formatDueDate, formatMinutes } from '../lib/format';

export function ProgressRoute() {
  const progress = useProgress();
  const summary = progress.data;

  return (
    <div className="stack">
      <PageHeading kicker="Evidence Ledger" title="What the record shows" />

      <QueryState
        isLoading={progress.isLoading}
        isError={progress.isError}
        error={progress.error}
        loadingLabel="Balancing the ledger…"
      >
        {summary ? (
          <div className="stack">
            <Panel title="Standing" eyebrow="Totals to date">
              <div className="ledger-figures">
                <div className="ledger-figure">
                  <div className="ledger-figure__value">{summary.streak_days}</div>
                  <div className="ledger-figure__unit">day streak</div>
                </div>
                <div className="ledger-figure">
                  <div className="ledger-figure__value">
                    {formatMinutes(summary.total_time_minutes)}
                  </div>
                  <div className="ledger-figure__unit">time on the bench</div>
                </div>
                <div className="ledger-figure">
                  <div className="ledger-figure__value">{summary.concepts.length}</div>
                  <div className="ledger-figure__unit">concepts on file</div>
                </div>
              </div>
              <p className="status-note status-note--info" style={{ marginTop: 'var(--space-4)' }}>
                Next: {summary.next_recommended_action}
              </p>
            </Panel>

            <Panel title="Concept evidence" eyebrow="Stamped mastery per concept">
              {summary.concepts.length > 0 ? (
                <ul className="card-list">
                  {summary.concepts.map((concept) => (
                    <li key={concept.id}>
                      <div className="evidence-row">
                        <div style={{ flex: 1 }}>
                          <MasteryMeter
                            concept={concept.id}
                            mastery={concept.mastery}
                            label={concept.label}
                          />
                        </div>
                      </div>
                      <p className="index-card__meta">
                        review {formatDueDate(concept.review_due_at)}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">No concepts recorded yet.</p>
              )}
            </Panel>

            {summary.recent_mistakes.length > 0 ? (
              <Panel title="Recent mistakes" eyebrow="Filed against the record" tone="ink">
                <ul className="mistake-inbox">
                  {summary.recent_mistakes.map((mistake, index) => (
                    <li key={index}>{mistake}</li>
                  ))}
                </ul>
              </Panel>
            ) : null}
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}
