import type { Hint } from '../contracts';
import { CommandButton } from './CommandButton';

export interface HintLadderProps {
  hints: Hint[];
  revealed: number;
  onReveal: () => void;
}

/** Hints climb one rung at a time. Each reveal is a deliberate choice because
 *  hints cost mastery on submit, so locked rungs stay locked until asked for. */
export function HintLadder({ hints, revealed, onReveal }: HintLadderProps) {
  if (hints.length === 0) {
    return <p className="muted">No hints for this exercise.</p>;
  }

  const ordered = [...hints].sort((a, b) => a.level - b.level);
  const shown = ordered.slice(0, revealed);
  const remaining = ordered.length - shown.length;

  return (
    <div className="hint-ladder">
      {shown.map((hint) => (
        <div className="hint-ladder__rung" key={hint.level}>
          <h4>Hint {hint.level}</h4>
          <p className="hint-ladder__text">{hint.text}</p>
        </div>
      ))}
      {remaining > 0 ? (
        <CommandButton variant="ghost" onClick={onReveal}>
          Reveal hint {shown.length + 1} of {ordered.length}
        </CommandButton>
      ) : (
        <p className="hint-ladder__locked">All {ordered.length} hints revealed.</p>
      )}
    </div>
  );
}
