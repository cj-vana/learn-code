import { describe, expect, it } from 'vitest';
import { masteryLabel } from './format';

describe('masteryLabel', () => {
  it('maps a 0-100 score to the same bands the server uses', () => {
    expect(masteryLabel(0)).toBe('new');
    expect(masteryLabel(19)).toBe('new');
    expect(masteryLabel(20)).toBe('learning');
    expect(masteryLabel(49)).toBe('learning');
    expect(masteryLabel(50)).toBe('practicing');
    expect(masteryLabel(74)).toBe('practicing');
    expect(masteryLabel(75)).toBe('review_ready');
    expect(masteryLabel(89)).toBe('review_ready');
    expect(masteryLabel(90)).toBe('interview_ready');
    expect(masteryLabel(100)).toBe('interview_ready');
  });
});
