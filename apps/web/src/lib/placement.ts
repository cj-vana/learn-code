import type { PathSummary } from '../contracts';

export interface StretchPath {
  path: PathSummary;
  missing: string[];
}

export interface Placement {
  /** Paths the learner can start today, most advanced first. */
  ready: PathSummary[];
  /** Paths missing at most two known-concept gaps, fewest gaps first. */
  stretch: StretchPath[];
}

/**
 * Every concept any path assumes, ordered by how many paths assume it.
 * The most widely assumed concepts are the most fundamental, so they
 * come first in the checklist.
 */
export function conceptChoices(paths: PathSummary[]): string[] {
  const counts = new Map<string, number>();
  for (const path of paths) {
    for (const concept of path.assumed_concepts) {
      counts.set(concept, (counts.get(concept) ?? 0) + 1);
    }
  }
  return [...counts.keys()].sort(
    (a, b) => (counts.get(b) ?? 0) - (counts.get(a) ?? 0) || a.localeCompare(b),
  );
}

/**
 * Recommend starting points from what the learner already knows. A path is
 * ready when everything it assumes is known; among ready paths the ones that
 * build on the most prior knowledge come first, career paths ahead of skill
 * paths on ties. With nothing selected only assume-nothing paths qualify,
 * which is exactly the beginner case.
 */
export function place(paths: PathSummary[], known: ReadonlySet<string>): Placement {
  const ready: PathSummary[] = [];
  const stretch: StretchPath[] = [];
  for (const path of paths) {
    const missing = path.assumed_concepts.filter((concept) => !known.has(concept));
    if (missing.length === 0) {
      ready.push(path);
    } else if (missing.length <= 2) {
      stretch.push({ path, missing });
    }
  }
  ready.sort(
    (a, b) =>
      b.assumed_concepts.length - a.assumed_concepts.length ||
      (a.path_type === b.path_type ? a.title.localeCompare(b.title) : a.path_type === 'career' ? -1 : 1),
  );
  stretch.sort((a, b) => a.missing.length - b.missing.length || a.path.title.localeCompare(b.path.title));
  return { ready, stretch };
}
