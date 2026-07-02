import { humanizeConcept } from '../lib/format';

export interface PatternChipProps {
  pattern: string;
  pressed?: boolean;
  onToggle?: (pattern: string) => void;
}

/** A small blueprint-colored tag for an algorithmic pattern / concept. When
 *  `onToggle` is provided it becomes a real toggle button (used to predict the
 *  pattern on the Solve Bench); otherwise it is a static label. */
export function PatternChip({ pattern, pressed, onToggle }: PatternChipProps) {
  const label = humanizeConcept(pattern);
  if (!onToggle) {
    return <span className="pattern-chip">{label}</span>;
  }
  return (
    <button
      type="button"
      className="pattern-chip"
      aria-pressed={pressed ?? false}
      onClick={() => onToggle(pattern)}
    >
      {label}
    </button>
  );
}
