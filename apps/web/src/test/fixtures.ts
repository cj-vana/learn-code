import type {
  ContentDetail,
  ContentSummary,
  OllamaReview,
  PlanItem,
  ProgressSummary,
  RunResult,
  SubmissionResponse,
} from '../contracts';

export const planFixture: PlanItem[] = [
  {
    id: 'plan-1',
    kind: 'exercise',
    content_id: 'two-sum',
    title: 'Two Sum',
    concepts: ['hash_map', 'arrays'],
    priority: 0.92,
    estimated_time_minutes: 20,
    rationale: {
      reason: 'You have not attempted hash-map lookups yet.',
      because: ['hash_map mastery is 0', 'arrays is a prerequisite you have met'],
      alternatives: ['A binary-search drill was lower yield today.'],
    },
  },
  {
    id: 'plan-2',
    kind: 'review',
    content_id: 'valid-parentheses',
    title: 'Valid Parentheses',
    concepts: ['stack'],
    priority: 0.6,
    estimated_time_minutes: 15,
    rationale: {
      reason: 'A stack review is due today.',
      because: ['stack review_due_at has passed'],
      alternatives: [],
    },
  },
];

export const progressFixture: ProgressSummary = {
  streak_days: 4,
  total_time_minutes: 145,
  concepts: [
    { id: 'hash_map', mastery: 62, label: 'practicing', review_due_at: null },
    {
      id: 'stack',
      mastery: 80,
      label: 'review_ready',
      review_due_at: '2026-07-01T00:00:00Z',
    },
  ],
  recent_mistakes: ['off_by_one', 'stack'],
  next_recommended_action: 'Drill hash-map lookups with Two Sum.',
};

export const contentListFixture: ContentSummary[] = [
  {
    id: 'two-sum',
    kind: 'exercise',
    title: 'Two Sum',
    slug: 'two-sum',
    difficulty: 'easy',
    concepts: ['hash_map', 'arrays'],
    prerequisites: [],
    estimated_time_minutes: 20,
  },
];

export const contentDetailFixture: ContentDetail = {
  id: 'two-sum',
  kind: 'exercise',
  version: 3,
  language: 'python',
  title: 'Two Sum',
  slug: 'two-sum',
  difficulty: 'easy',
  concepts: ['hash_map', 'arrays'],
  prerequisites: [],
  estimated_time_minutes: 20,
  prompt_markdown: 'Return indices of the two numbers that add up to target.',
  starter_code: 'def two_sum(nums, target):\n    pass\n',
  function_name: 'two_sum',
  input_mode: 'args',
  hints: [
    { level: 1, text: 'A hash map trades space for time.' },
    { level: 2, text: 'Store each value you have seen and its index.' },
  ],
  public_tests: [{ name: 'example_1', input: [[2, 7], 9], expected: [0, 1] }],
  common_mistakes: ['Using a nested loop is O(n^2).'],
};

export const passingRunFixture: RunResult = {
  status: 'passed',
  passed: 1,
  failed: 0,
  stdout: '',
  stderr: '',
  duration_ms: 42,
  test_summary: [
    { name: 'example_1', visibility: 'public', passed: true, message: null },
  ],
};

export const submissionFixture: SubmissionResponse = {
  submission_id: 'sub-123',
  run: passingRunFixture,
  progress_delta: {
    concepts_changed: ['hash_map'],
    mastery_before: 54,
    mastery_after: 62,
    review_due_at: '2026-07-03T00:00:00Z',
  },
  next_actions: ['Review the stack pattern next.'],
};

export const availableReviewFixture: OllamaReview = {
  status: 'available',
  summary: 'Clean use of a dictionary; solid work.',
  correctness_notes: [],
  readability_notes: ['Naming is clear.'],
  python_simplifications: [],
  big_o_notes: 'O(n) time, O(n) space.',
  next_improvement: 'Guard against empty input.',
  encouragement: 'Nice — you nailed the pattern.',
  solution_disclosed: false,
};
