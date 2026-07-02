import { describe, expect, it } from 'vitest';
import { contentHref, masteryLabel } from './format';

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

describe('contentHref', () => {
  it('routes each kind to its page', () => {
    expect(contentHref('lesson', 'lesson.l1')).toBe('/lesson/lesson.l1');
    expect(contentHref('quiz', 'quiz.q1')).toBe('/quiz/quiz.q1');
    expect(contentHref('exercise', 'exercise.e1')).toBe('/exercise/exercise.e1');
    expect(contentHref('review', 'exercise.e1')).toBe('/exercise/exercise.e1');
  });
});
