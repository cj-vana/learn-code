import { describe, expect, it } from 'vitest';
import type { PathSummary } from '../contracts';
import { conceptChoices, place } from './placement';

function summary(over: Partial<PathSummary>): PathSummary {
  return {
    id: 'path.skill.x',
    path_type: 'skill',
    level: 'beginner',
    title: 'X',
    slug: 'x',
    description: 'd',
    outcomes: ['o'],
    assumed_concepts: [],
    estimated_hours: 5,
    units: 2,
    items: 40,
    enrolled: false,
    percent_complete: 0,
    ...over,
  };
}

const FOUNDATIONS = summary({ id: 'p.foundations', title: 'Foundations' });
const REGEX = summary({
  id: 'p.regex',
  title: 'Regex',
  assumed_concepts: ['Functions', 'Strings'],
});
const INTERNALS = summary({
  id: 'p.internals',
  title: 'Internals',
  assumed_concepts: ['Functions', 'Strings', 'Classes', 'Exceptions'],
});
const CAREER = summary({
  id: 'p.career',
  title: 'Career Arc',
  path_type: 'career',
  assumed_concepts: ['Functions', 'Strings'],
});

describe('conceptChoices', () => {
  it('orders concepts by how many paths assume them', () => {
    const choices = conceptChoices([FOUNDATIONS, REGEX, INTERNALS, CAREER]);
    expect(choices.slice(0, 2)).toEqual(['Functions', 'Strings']);
    expect(choices).toContain('Classes');
  });
});

describe('place', () => {
  it('recommends only assume-nothing paths to a brand-new learner', () => {
    const { ready } = place([FOUNDATIONS, REGEX, INTERNALS], new Set());
    expect(ready.map((p) => p.id)).toEqual(['p.foundations']);
  });

  it('puts the most advanced eligible path first, career ahead on ties', () => {
    const known = new Set(['Functions', 'Strings', 'Classes', 'Exceptions']);
    const { ready } = place([FOUNDATIONS, REGEX, INTERNALS, CAREER], known);
    expect(ready.map((p) => p.id)).toEqual(['p.internals', 'p.career', 'p.regex', 'p.foundations']);
  });

  it('lists near-miss paths as stretch with their gaps', () => {
    const { ready, stretch } = place([REGEX, INTERNALS], new Set(['Functions']));
    expect(ready).toEqual([]);
    expect(stretch.map((s) => s.path.id)).toEqual(['p.regex']);
    expect(stretch[0].missing).toEqual(['Strings']);
  });
});
