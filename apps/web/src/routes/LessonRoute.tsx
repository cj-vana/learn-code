import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useCompleteLesson, useLessonDetail } from '../api/queries';
import type { CheckpointDetail } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';
import { formatMinutes } from '../lib/format';

function Checkpoint({ checkpoint, index }: { checkpoint: CheckpointDetail; index: number }) {
  const [revealed, setRevealed] = useState(false);
  return (
    <article className="index-card index-card--lesson">
      <p className="index-card__meta">Checkpoint {index + 1}</p>
      <h3 className="index-card__title">{checkpoint.question}</h3>
      {revealed ? (
        <div className="stack">
          <p>{checkpoint.answer}</p>
          <p className="muted">{checkpoint.explanation}</p>
        </div>
      ) : (
        <div className="command-row" style={{ marginTop: 'var(--space-2)' }}>
          <button className="command-btn" type="button" onClick={() => setRevealed(true)}>
            Reveal the answer
          </button>
        </div>
      )}
    </article>
  );
}

export function LessonRoute() {
  const { id } = useParams<{ id: string }>();
  const lesson = useLessonDetail(id);
  const complete = useCompleteLesson();
  const detail = lesson.data;

  return (
    <div className="stack">
      <PageHeading kicker="Bench Notes" title={detail?.title ?? 'Lesson'} />

      <QueryState
        isLoading={lesson.isLoading}
        isError={lesson.isError}
        error={lesson.error}
        loadingLabel="Opening the notes…"
      >
        {detail ? (
          <div className="stack">
            <Panel
              title="The lesson"
              eyebrow={`${detail.difficulty} · ${formatMinutes(detail.estimated_time_minutes)}`}
            >
              <div className="chip-row" style={{ marginBottom: 'var(--space-3)' }}>
                {detail.concepts.map((concept) => (
                  <PatternChip key={concept} pattern={concept} />
                ))}
              </div>
              <div className="prose" style={{ whiteSpace: 'pre-wrap' }}>
                {detail.body_markdown}
              </div>
            </Panel>

            <Panel title="Checkpoints" eyebrow="Check yourself before moving on">
              <ul className="card-list">
                {detail.checkpoints.map((checkpoint, index) => (
                  <li key={index}>
                    <Checkpoint checkpoint={checkpoint} index={index} />
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel title="File it" eyebrow="Done reading?">
              {complete.isSuccess ? (
                <div className="stack">
                  <p>Lesson filed. It will not queue again.</p>
                  <div className="command-row">
                    <Link className="command-btn command-btn--pine" to="/learn">
                      Back to the bench
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="command-row">
                  <button
                    className="command-btn command-btn--pine"
                    type="button"
                    disabled={complete.isPending}
                    onClick={() => complete.mutate(detail.id)}
                  >
                    Mark lesson complete
                  </button>
                </div>
              )}
              {complete.isError ? (
                <p className="muted">Could not record completion. Try again.</p>
              ) : null}
            </Panel>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}
