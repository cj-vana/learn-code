import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  activeTimedSession,
  advance,
  elapsedSeconds,
  type TimedSessionState,
} from '../lib/timedSession';
import { contentHref } from '../lib/format';
import { Panel } from './Panel';

function formatClock(totalSeconds: number): string {
  const sign = totalSeconds < 0 ? '-' : '';
  const seconds = Math.abs(totalSeconds);
  return `${sign}${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

/** Countdown strip shown on an exercise page while a timed session covers it.
 *  Advisory only: running past zero flips to "over time", nothing is blocked. */
export function TimedBanner({
  exerciseId,
  session,
}: {
  exerciseId: string;
  session: TimedSessionState;
}) {
  const [, tick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => tick((count) => count + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const index = session.exercises.findIndex((exercise) => exercise.id === exerciseId);
  if (index === -1) return null;

  const budget = session.minutes_per_problem * 60;
  const remaining = budget - elapsedSeconds(exerciseId);
  const nextExercise = session.exercises[index + 1];

  return (
    <Panel
      title={`Timed practice · problem ${index + 1} of ${session.exercises.length}`}
      eyebrow={remaining >= 0 ? `${formatClock(remaining)} on the clock` : `over time by ${formatClock(-remaining)}`}
      tone="ink"
    >
      <div className="command-row">
        {nextExercise ? (
          <Link
            className="command-btn"
            to={contentHref('exercise', nextExercise.id)}
            onClick={() => advance()}
          >
            Next problem →
          </Link>
        ) : (
          <Link className="command-btn" to="/timed" onClick={() => advance()}>
            Finish session
          </Link>
        )}
      </div>
    </Panel>
  );
}

export function useActiveTimedSession(exerciseId: string | undefined) {
  const [session, setSession] = useState<TimedSessionState | null>(null);
  useEffect(() => {
    setSession(activeTimedSession());
  }, [exerciseId]);
  return session;
}
