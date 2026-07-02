import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useStartTimedSession } from '../api/queries';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import {
  activeTimedSession,
  clearTimedSession,
  elapsedSeconds,
  sessionFinished,
  startTimedSession,
} from '../lib/timedSession';
import { contentHref } from '../lib/format';

const COUNTS = [2, 3, 5];
const BUDGETS = [10, 15, 20];

export function TimedRoute() {
  const navigate = useNavigate();
  const start = useStartTimedSession();
  const [count, setCount] = useState(3);
  const [minutes, setMinutes] = useState(15);
  const [, refresh] = useState(0);

  const session = activeTimedSession();

  const onStart = () => {
    start.mutate(
      { count, minutes_per_problem: minutes },
      {
        onSuccess: (response) => {
          if (response.exercises.length === 0) {
            refresh((n) => n + 1);
            return;
          }
          const state = startTimedSession(response);
          navigate(contentHref('exercise', state.exercises[0].id));
        },
      },
    );
  };

  const emptyResult = start.isSuccess && start.data.exercises.length === 0;

  return (
    <div className="stack">
      <PageHeading kicker="Stopwatch Bench" title="Timed practice" />

      {session ? (
        <Panel
          title={sessionFinished(session) ? 'Session summary' : 'Session in progress'}
          eyebrow={`${session.exercises.length} problems · ${session.minutes_per_problem} min each`}
        >
          <ul className="card-list">
            {session.exercises.map((exercise) => {
              const status = session.outcomes[exercise.id];
              const used = elapsedSeconds(exercise.id);
              const budget = session.minutes_per_problem * 60;
              const overTime = used > budget;
              return (
                <li key={exercise.id}>
                  <article className="index-card index-card--exercise">
                    <p className="index-card__meta">
                      {status ? (status === 'passed' ? 'passed' : status) : 'not submitted'} ·{' '}
                      {Math.floor(used / 60)}m used of {session.minutes_per_problem}m
                      {overTime ? ' · over time' : ''}
                    </p>
                    <h3 className="index-card__title">
                      <Link to={contentHref('exercise', exercise.id)}>{exercise.title}</Link>
                    </h3>
                  </article>
                </li>
              );
            })}
          </ul>
          <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
            <button
              className="command-btn"
              type="button"
              onClick={() => {
                clearTimedSession();
                refresh((n) => n + 1);
              }}
            >
              Clear session
            </button>
          </div>
        </Panel>
      ) : (
        <Panel title="Set the clock" eyebrow="Advisory timing — nothing blocks you">
          <fieldset className="field">
            <legend>Problems</legend>
            <div className="chip-row" role="group" aria-label="Problem count">
              {COUNTS.map((value) => (
                <button
                  key={value}
                  className="command-btn"
                  type="button"
                  aria-pressed={count === value}
                  onClick={() => setCount(value)}
                >
                  {value}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset className="field">
            <legend>Minutes per problem</legend>
            <div className="chip-row" role="group" aria-label="Minutes per problem">
              {BUDGETS.map((value) => (
                <button
                  key={value}
                  className="command-btn"
                  type="button"
                  aria-pressed={minutes === value}
                  onClick={() => setMinutes(value)}
                >
                  {value}
                </button>
              ))}
            </div>
          </fieldset>
          <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
            <button
              className="command-btn command-btn--pine"
              type="button"
              disabled={start.isPending}
              onClick={onStart}
            >
              Start timed session
            </button>
          </div>
          {emptyResult ? (
            <p className="muted">
              Nothing is timed-ready yet — get a few concepts to practicing mastery first.
            </p>
          ) : null}
        </Panel>
      )}
    </div>
  );
}
