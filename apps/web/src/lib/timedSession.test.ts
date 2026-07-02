import { beforeEach, describe, expect, it } from 'vitest';
import {
  activeTimedSession,
  advance,
  clearTimedSession,
  currentProblem,
  elapsedSeconds,
  recordOutcome,
  startTimedSession,
} from './timedSession';
import type { TimedSessionResponse } from '../contracts';

const RESPONSE: TimedSessionResponse = {
  session_id: 'timed-1',
  minutes_per_problem: 10,
  exercises: [
    { id: 'ex.a', title: 'A', concepts: [], estimated_time_minutes: 8 },
    { id: 'ex.b', title: 'B', concepts: [], estimated_time_minutes: 8 },
  ],
};

beforeEach(() => {
  sessionStorage.clear();
});

describe('timedSession', () => {
  it('starts, tracks the current problem, and advances', () => {
    expect(activeTimedSession()).toBeNull();
    startTimedSession(RESPONSE);

    const session = activeTimedSession();
    expect(session?.session_id).toBe('timed-1');
    expect(currentProblem()?.id).toBe('ex.a');

    recordOutcome('ex.a', 'passed');
    advance();
    expect(currentProblem()?.id).toBe('ex.b');

    recordOutcome('ex.b', 'failed_tests');
    advance();
    expect(currentProblem()).toBeNull();
    expect(activeTimedSession()?.outcomes).toEqual({
      'ex.a': 'passed',
      'ex.b': 'failed_tests',
    });
  });

  it('tracks elapsed seconds per problem and clears', () => {
    startTimedSession(RESPONSE);
    expect(elapsedSeconds('ex.a')).toBeGreaterThanOrEqual(0);
    clearTimedSession();
    expect(activeTimedSession()).toBeNull();
  });
});
