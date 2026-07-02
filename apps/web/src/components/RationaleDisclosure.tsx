import type { Rationale } from '../contracts';

export interface RationaleDisclosureProps {
  rationale: Rationale;
  summaryLabel?: string;
}

/** The planner's "show your working": why this item was chosen, the evidence
 *  behind it, and what was considered instead. Collapsed by default. */
export function RationaleDisclosure({
  rationale,
  summaryLabel = 'Why this, why now',
}: RationaleDisclosureProps) {
  return (
    <details className="rationale">
      <summary>{summaryLabel}</summary>
      <div className="rationale__body">
        <p>{rationale.reason}</p>
        {rationale.because.length > 0 ? (
          <>
            <h4>Because</h4>
            <ul>
              {rationale.because.map((line, index) => (
                <li key={index}>{line}</li>
              ))}
            </ul>
          </>
        ) : null}
        {rationale.alternatives.length > 0 ? (
          <>
            <h4>Considered instead</h4>
            <ul>
              {rationale.alternatives.map((line, index) => (
                <li key={index}>{line}</li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
    </details>
  );
}
