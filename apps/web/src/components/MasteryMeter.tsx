import type { MasteryLabel } from '../contracts';
import { humanizeConcept } from '../lib/format';

export interface MasteryMeterProps {
  concept: string;
  mastery: number;
  label: MasteryLabel;
}

const LABEL_TEXT: Record<MasteryLabel, string> = {
  new: 'New',
  learning: 'Learning',
  practicing: 'Practicing',
  review_ready: 'Review ready',
  interview_ready: 'Interview ready',
};

/** A ruled mastery gauge with a rubber-stamp label — the ledger's evidence that
 *  a concept has been drilled. */
export function MasteryMeter({ concept, mastery, label }: MasteryMeterProps) {
  const clamped = Math.max(0, Math.min(100, mastery));
  return (
    <div className="mastery-meter">
      <div className="mastery-meter__head">
        <span className="mastery-meter__label">{humanizeConcept(concept)}</span>
        <span className="mastery-meter__stamp" data-label={label}>
          {LABEL_TEXT[label]}
        </span>
      </div>
      <div
        className="mastery-meter__track"
        role="meter"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${humanizeConcept(concept)} mastery`}
      >
        <div className="mastery-meter__fill" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
