import { ApiConnectionError, ApiError } from '../api/client';

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
