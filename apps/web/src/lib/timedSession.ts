/*
 * Client-owned timed-practice state. Timing is advisory (spec Part 3): the
 * API selects the problems and mints the session id; the browser tracks per-
 * problem start times and outcomes in sessionStorage so a refresh mid-session
 * survives but a new tab starts clean.
 */

import type { TimedSessionResponse } from '../contracts';

const STORAGE_KEY = 'learn-code.timed-session';

export interface TimedSessionState {
  session_id: string;
  minutes_per_problem: number;
  exercises: TimedSessionResponse['exercises'];
  currentIndex: number;
  startedAt: Record<string, number>;
  outcomes: Record<string, string>;
}

function save(state: TimedSessionState): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function activeTimedSession(): TimedSessionState | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TimedSessionState;
  } catch {
    sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function startTimedSession(response: TimedSessionResponse): TimedSessionState {
  const state: TimedSessionState = {
    session_id: response.session_id,
    minutes_per_problem: response.minutes_per_problem,
    exercises: response.exercises,
    currentIndex: 0,
    startedAt: response.exercises.length
      ? { [response.exercises[0].id]: Date.now() }
      : {},
    outcomes: {},
  };
  save(state);
  return state;
}

export function currentProblem(): TimedSessionResponse['exercises'][number] | null {
  const state = activeTimedSession();
  if (!state) return null;
  return state.exercises[state.currentIndex] ?? null;
}

export function recordOutcome(exerciseId: string, status: string): void {
  const state = activeTimedSession();
  if (!state) return;
  state.outcomes[exerciseId] = status;
  save(state);
}

export function advance(): void {
  const state = activeTimedSession();
  if (!state) return;
  state.currentIndex += 1;
  const next = state.exercises[state.currentIndex];
  if (next && state.startedAt[next.id] === undefined) {
    state.startedAt[next.id] = Date.now();
  }
  save(state);
}

export function elapsedSeconds(exerciseId: string): number {
  const state = activeTimedSession();
  const startedAt = state?.startedAt[exerciseId];
  if (startedAt === undefined) return 0;
  return Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
}

export function sessionFinished(state: TimedSessionState): boolean {
  return state.currentIndex >= state.exercises.length;
}

export function clearTimedSession(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
