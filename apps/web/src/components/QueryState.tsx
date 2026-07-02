import type { ReactNode } from 'react';
import { describeError } from '../lib/format';

export interface QueryStateProps {
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
  loadingLabel?: string;
  children: ReactNode;
}

/** Consistent loading / error framing for a data-backed panel, in the paper
 *  workshop's voice. Errors surface the API envelope message but never the raw
 *  stack. */
export function QueryState({
  isLoading,
  isError,
  error,
  loadingLabel = 'Pulling the ledger…',
  children,
}: QueryStateProps) {
  if (isLoading) {
    return <p className="muted">{loadingLabel}</p>;
  }
  if (isError) {
    return (
      <p className="status-note status-note--error" role="alert">
        {describeError(error)}
      </p>
    );
  }
  return <>{children}</>;
}
