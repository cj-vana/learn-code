/*
 * TypeScript mirror of `apps/api/learn_code_api/contracts/__init__.py`.
 *
 * These types are the single source of truth for the shapes the web client
 * reads and writes. They must not drift from the Python contracts: only fields
 * the API actually returns appear here. V1 supports only `language: 'python'`.
 */

export type RunStatus =
  | 'passed'
  | 'failed_tests'
  | 'syntax_error'
  | 'runtime_error'
  | 'timeout'
  | 'memory_exceeded'
  | 'output_exceeded'
  | 'internal_error';

export type PlanKind = 'lesson' | 'exercise' | 'quiz' | 'review';

export type MasteryLabel =
  | 'new'
  | 'learning'
  | 'practicing'
  | 'review_ready'
  | 'interview_ready';

export type TestVisibility = 'public' | 'validation';

export interface HealthResponse {
  status: 'ok';
}

export interface Rationale {
  reason: string;
  because: string[];
  alternatives: string[];
}

export interface PlanItem {
  id: string;
  kind: PlanKind;
  content_id: string;
  title: string;
  concepts: string[];
  priority: number;
  estimated_time_minutes: number;
  rationale: Rationale;
}

export interface ConceptSummary {
  id: string;
  mastery: number;
  label: MasteryLabel;
  review_due_at: string | null;
}

export interface ProgressSummary {
  streak_days: number;
  total_time_minutes: number;
  concepts: ConceptSummary[];
  recent_mistakes: string[];
  next_recommended_action: string;
}

export interface PublicTestCase {
  name: string;
  input: unknown;
  expected: unknown;
}

export interface ContentSummary {
  id: string;
  kind: string;
  title: string;
  slug: string;
  difficulty: string;
  concepts: string[];
  prerequisites: string[];
  estimated_time_minutes: number;
}

export interface Hint {
  level: number;
  text: string;
}

export interface ContentDetail {
  id: string;
  kind: string;
  version: number;
  language: string;
  title: string;
  slug: string;
  difficulty: string;
  concepts: string[];
  prerequisites: string[];
  estimated_time_minutes: number;
  prompt_markdown: string;
  starter_code: string;
  function_name: string;
  input_mode: string;
  hints: Hint[];
  public_tests: PublicTestCase[];
  common_mistakes: string[];
}

export interface TestSummaryEntry {
  name: string;
  visibility: TestVisibility;
  passed: boolean;
  message: string | null;
}

export interface RunResult {
  status: RunStatus;
  passed: number;
  failed: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
  test_summary: TestSummaryEntry[];
}

export interface PublicRunRequest {
  exercise_id: string;
  language: 'python';
  source: string;
}

export interface PlaygroundRunRequest {
  language: 'python';
  source: string;
  stdin?: string | null;
}

export interface ExerciseSubmissionRequest {
  exercise_id: string;
  content_version: number;
  language: 'python';
  source: string;
  predicted_pattern?: string | null;
  confidence?: number | null;
  hints_used?: number;
  timed_session_id?: string | null;
}

export interface ProgressDelta {
  concepts_changed: string[];
  mastery_before: number;
  mastery_after: number;
  review_due_at: string | null;
}

export interface SubmissionResponse {
  submission_id: string;
  run: RunResult;
  progress_delta: ProgressDelta;
  next_actions: string[];
}

export interface QuizAnswerRequest {
  quiz_id: string;
  question_id: string;
  choice: string;
}

export interface CheckpointDetail {
  question: string;
  answer: string;
  explanation: string;
}

export interface LessonDetail {
  id: string;
  kind: 'lesson';
  version: number;
  language: string;
  title: string;
  slug: string;
  difficulty: string;
  concepts: string[];
  prerequisites: string[];
  estimated_time_minutes: number;
  body_markdown: string;
  checkpoints: CheckpointDetail[];
}

export interface QuizQuestionDetail {
  id: string;
  prompt: string;
  choices: string[];
  concepts: string[];
}

export interface QuizDetail {
  id: string;
  kind: 'quiz';
  version: number;
  language: string;
  title: string;
  slug: string;
  difficulty: string;
  concepts: string[];
  prerequisites: string[];
  estimated_time_minutes: number;
  quiz_type: string;
  questions: QuizQuestionDetail[];
}

export interface LessonCompletionResponse {
  lesson_id: string;
  completed_at: string;
}

export interface PathItemStatus {
  id: string;
  kind: string;
  title: string;
  estimated_time_minutes: number;
  status: 'todo' | 'complete';
}

export interface PathUnitDetail {
  id: string;
  title: string;
  description: string;
  items: PathItemStatus[];
  percent_complete: number;
}

export interface PathSummary {
  id: string;
  path_type: string;
  title: string;
  slug: string;
  description: string;
  outcomes: string[];
  estimated_hours: number;
  units: number;
  items: number;
  enrolled: boolean;
  percent_complete: number;
}

export interface PathDetail {
  id: string;
  path_type: string;
  title: string;
  slug: string;
  description: string;
  outcomes: string[];
  estimated_hours: number;
  enrolled: boolean;
  percent_complete: number;
  units: PathUnitDetail[];
  next_item_id: string | null;
}

export interface PathEnrollmentResponse {
  path_id: string;
  enrolled: boolean;
}

export interface TimedSessionRequest {
  concept_filter?: string | null;
  count?: number;
  minutes_per_problem?: number;
}

export interface TimedSessionExercise {
  id: string;
  title: string;
  concepts: string[];
  estimated_time_minutes: number;
}

export interface TimedSessionResponse {
  session_id: string;
  minutes_per_problem: number;
  exercises: TimedSessionExercise[];
}

export interface QuizAnswerResponse {
  question_id: string;
  correct: boolean;
  explanation: string;
  concepts_changed: string[];
  next_review_due_at: string | null;
}

export interface ReviewRequest {
  exercise_id: string;
  source: string;
  test_result_summary?: string;
  allow_solution_disclosure?: boolean;
}

export type ReviewStatus = 'available' | 'unavailable' | 'model_missing' | 'error';

export interface OllamaReview {
  status: ReviewStatus;
  summary: string;
  correctness_notes: string[];
  readability_notes: string[];
  python_simplifications: string[];
  big_o_notes: string | null;
  next_improvement: string | null;
  encouragement: string | null;
  solution_disclosed: boolean;
}

export type ErrorCode =
  | 'content_not_found'
  | 'validation_error'
  | 'runner_unavailable'
  | 'ollama_unavailable'
  | 'internal_error';

export interface ErrorBody {
  code: ErrorCode;
  message: string;
  details: Record<string, unknown>;
}

export interface ErrorEnvelope {
  error: ErrorBody;
}
