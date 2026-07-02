import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  useContentDetail,
  useRequestReview,
  useRunExercise,
  useSubmitExercise,
} from '../api/queries';
import type { RunResult } from '../contracts';
import { CodeEditor } from '../editor/CodeEditor';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';
import { CommandButton } from '../components/CommandButton';
import { TestReceipt } from '../components/TestReceipt';
import { HintLadder } from '../components/HintLadder';
import { MasteryMeter } from '../components/MasteryMeter';
import { describeError, formatMinutes, humanizeConcept, masteryLabel } from '../lib/format';

const CONFIDENCE_LEVELS = [1, 2, 3, 4, 5];

function summarizeForReview(result: RunResult | null): string {
  if (!result) return 'not provided';
  return `${result.status}: ${result.passed} passed, ${result.failed} failed`;
}

export function ExerciseRoute() {
  const { id } = useParams<{ id: string }>();
  const content = useContentDetail(id);

  const [source, setSource] = useState('');
  const initializedFor = useRef<string | null>(null);
  const [predictedPattern, setPredictedPattern] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [revealedHints, setRevealedHints] = useState(0);

  const run = useRunExercise();
  const submit = useSubmitExercise();
  const review = useRequestReview();

  const detail = content.data;

  useEffect(() => {
    if (detail && initializedFor.current !== detail.id) {
      setSource(detail.starter_code);
      initializedFor.current = detail.id;
      setPredictedPattern(null);
      setConfidence(null);
      setRevealedHints(0);
      run.reset();
      submit.reset();
      review.reset();
    }
    // Only re-seed when the loaded exercise changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail]);

  const latestRun: RunResult | null = submit.data?.run ?? run.data ?? null;

  const togglePattern = (pattern: string) => {
    setPredictedPattern((prev) => (prev === pattern ? null : pattern));
  };

  const onRun = () => {
    if (!id) return;
    run.mutate({ exercise_id: id, language: 'python', source });
  };

  const onSubmit = () => {
    if (!id || !detail) return;
    submit.mutate({
      exercise_id: id,
      content_version: detail.version,
      language: 'python',
      source,
      predicted_pattern: predictedPattern,
      confidence,
      hints_used: revealedHints,
    });
  };

  const onRequestReview = () => {
    if (!id) return;
    review.mutate({
      exercise_id: id,
      source,
      test_result_summary: summarizeForReview(latestRun),
      allow_solution_disclosure: false,
    });
  };

  const reviewData = review.data;

  const conceptChips = useMemo(() => detail?.concepts ?? [], [detail]);

  return (
    <div className="stack">
      <PageHeading kicker="Solve Bench" title={detail?.title ?? 'Exercise'} />

      <QueryState
        isLoading={content.isLoading}
        isError={content.isError}
        error={content.error}
        loadingLabel="Fetching the exercise…"
      >
        {detail ? (
          <div className="page-grid page-grid--solve">
            <div className="stack">
              <Panel
                title="The problem"
                eyebrow={`${detail.difficulty} · ${formatMinutes(
                  detail.estimated_time_minutes,
                )}`}
              >
                <div className="chip-row" style={{ marginBottom: 'var(--space-3)' }}>
                  {detail.concepts.map((concept) => (
                    <PatternChip key={concept} pattern={concept} />
                  ))}
                </div>
                <div className="prose" style={{ whiteSpace: 'pre-wrap' }}>
                  {detail.prompt_markdown}
                </div>
              </Panel>

              <Panel title="Bench notes" eyebrow="Hints climb one rung at a time">
                <HintLadder
                  hints={detail.hints}
                  revealed={revealedHints}
                  onReveal={() => setRevealedHints((count) => count + 1)}
                />
              </Panel>
            </div>

            <div className="stack">
              <Panel title="Prediction & confidence" eyebrow="Call it before you run it">
                <fieldset className="field">
                  <legend>Predict the pattern</legend>
                  <p className="field__hint">
                    A correct call before submitting earns extra mastery.
                  </p>
                  <div
                    className="chip-row"
                    role="group"
                    aria-label="Predicted pattern"
                  >
                    {conceptChips.map((concept) => (
                      <PatternChip
                        key={concept}
                        pattern={concept}
                        pressed={predictedPattern === concept}
                        onToggle={togglePattern}
                      />
                    ))}
                  </div>
                </fieldset>

                <fieldset className="field">
                  <legend>Confidence</legend>
                  <p className="field__hint">How sure are you, 1 (guessing) to 5 (certain)?</p>
                  <div className="confidence-scale">
                    {CONFIDENCE_LEVELS.map((level) => (
                      <label key={level}>
                        <input
                          type="radio"
                          name="confidence"
                          value={level}
                          checked={confidence === level}
                          onChange={() => setConfidence(level)}
                        />
                        {level}
                      </label>
                    ))}
                  </div>
                </fieldset>
              </Panel>

              <Panel title="Solution" eyebrow={`python · v${detail.version}`}>
                <div className="editor-frame">
                  <div className="editor-frame__caption">
                    <span>{detail.function_name}()</span>
                    <span>python</span>
                  </div>
                  <CodeEditor value={source} language="python" onChange={setSource} />
                </div>
                <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
                  <CommandButton
                    variant="ghost"
                    onClick={onRun}
                    busy={run.isPending}
                    aria-label="Run public tests"
                  >
                    Run public tests
                  </CommandButton>
                  <CommandButton
                    variant="pine"
                    onClick={onSubmit}
                    busy={submit.isPending}
                    aria-label="Submit for grading"
                  >
                    Submit solution
                  </CommandButton>
                </div>
                {run.isError ? (
                  <p className="status-note status-note--error" role="alert">
                    {describeError(run.error)}
                  </p>
                ) : null}
                {submit.isError ? (
                  <p className="status-note status-note--error" role="alert">
                    {describeError(submit.error)}
                  </p>
                ) : null}
              </Panel>

              {run.data && !submit.data ? (
                <Panel title="Run receipt" eyebrow="Public tests only">
                  <TestReceipt result={run.data} title="Public run" />
                </Panel>
              ) : null}

              {submit.data ? (
                <Panel title="Submission filed" eyebrow="Graded against validation tests">
                  <TestReceipt result={submit.data.run} title="Submission" />
                  <div style={{ marginTop: 'var(--space-4)' }}>
                    <MasteryMeter
                      concept={
                        submit.data.progress_delta.concepts_changed[0] ??
                        detail.concepts[0] ??
                        detail.id
                      }
                      mastery={submit.data.progress_delta.mastery_after}
                      label={masteryLabel(submit.data.progress_delta.mastery_after)}
                    />
                    <p className="muted" style={{ marginTop: 'var(--space-2)' }}>
                      Mastery {submit.data.progress_delta.mastery_before} →{' '}
                      {submit.data.progress_delta.mastery_after}
                    </p>
                  </div>
                  {submit.data.next_actions.length > 0 ? (
                    <ul className="mistake-inbox" style={{ marginTop: 'var(--space-3)' }}>
                      {submit.data.next_actions.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  ) : null}
                </Panel>
              ) : null}

              <Panel title="Mentor review" eyebrow="Optional · Ollama" tone="ink">
                <p className="field__hint" style={{ color: 'var(--paper)' }}>
                  A local model comments on style and complexity. Tests still decide
                  pass or fail — a review is never required.
                </p>
                <div className="command-row">
                  <CommandButton
                    variant="ochre"
                    onClick={onRequestReview}
                    busy={review.isPending}
                    aria-label="Request a mentor review"
                  >
                    Request review
                  </CommandButton>
                </div>
                {review.isError ? (
                  <p className="status-note status-note--info" role="status">
                    Review unavailable right now. Your run and submission still stand.
                  </p>
                ) : null}
                {reviewData ? (
                  <div style={{ marginTop: 'var(--space-3)' }}>
                    {reviewData.status !== 'available' ? (
                      <p className="status-note status-note--info" role="status">
                        Reviewer {reviewData.status.replace('_', ' ')} — {reviewData.summary}
                      </p>
                    ) : (
                      <div className="prose">
                        <p>{reviewData.summary}</p>
                        {reviewData.next_improvement ? (
                          <p>
                            <strong>Next:</strong> {reviewData.next_improvement}
                          </p>
                        ) : null}
                        {reviewData.encouragement ? (
                          <p className="muted">{reviewData.encouragement}</p>
                        ) : null}
                      </div>
                    )}
                  </div>
                ) : null}
              </Panel>
            </div>
          </div>
        ) : (
          <p className="status-note status-note--error" role="alert">
            Exercise not found. <Link to="/learn">Back to the bench.</Link> (
            {humanizeConcept(id ?? 'unknown')})
          </p>
        )}
      </QueryState>
    </div>
  );
}
