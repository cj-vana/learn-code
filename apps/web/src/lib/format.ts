import { ApiConnectionError, ApiError } from '../api/client';
import type { MasteryLabel } from '../contracts';

/** Mastery band for a 0-100 score. Mirrors the server-side thresholds
 *  (new 0-19, learning 20-49, practicing 50-74, review_ready 75-89,
 *  interview_ready 90-100) so a derived stamp matches the number beside it. */
export function masteryLabel(mastery: number): MasteryLabel {
  if (mastery >= 90) return 'interview_ready';
  if (mastery >= 75) return 'review_ready';
  if (mastery >= 50) return 'practicing';
  if (mastery >= 20) return 'learning';
  return 'new';
}

/** Human-readable message for anything thrown by the API client or fetch. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof ApiConnectionError) {
    return 'The API is not reachable. Start the stack with `docker compose up --build`.';
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong.';
}

export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours}h ${rest}m` : `${hours}h`;
}

/** Turn a snake_case concept id into a readable label. */
export function humanizeConcept(id: string): string {
  return id
    .split(/[_\-.]/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatDueDate(iso: string | null): string {
  if (!iso) return 'not scheduled';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
