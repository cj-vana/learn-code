import { useHealth, useUpdateStatus } from '../api/queries';

/** A thin instrument strip across the top of the workshop: is the runtime
 *  (the API + sandbox) live? It polls `/api/v1/health` and never blocks the UI —
 *  a red lamp is information, not an error page. */
export function RuntimeStatusStrip() {
  const { data, isError, isLoading, isFetching } = useHealth();
  const update = useUpdateStatus();

  let state: 'ok' | 'down' | 'checking';
  let label: string;
  if (isLoading) {
    state = 'checking';
    label = 'Checking runtime';
  } else if (isError || data?.status !== 'ok') {
    state = 'down';
    label = 'Runtime offline';
  } else {
    state = 'ok';
    label = 'Runtime live';
  }

  return (
    <div className="runtime-strip" role="status" aria-live="polite">
      <span className="runtime-strip__lamp" data-state={state} aria-hidden="true" />
      <span className="runtime-strip__label">{label}</span>
      <span>Learn Code · /api/v1</span>
      {update.data?.update_available ? (
        <span className="runtime-strip__meta">
          update available: {update.data.latest_version} — git pull, then docker compose up
          --build
        </span>
      ) : null}
      <span className="runtime-strip__meta">
        {state === 'down'
          ? 'docker compose up --build'
          : isFetching
            ? 'polling…'
            : 'sandboxed python runner'}
      </span>
    </div>
  );
}
