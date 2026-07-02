import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders, type RecordedCall } from '../test/utils';
import type { QuizDetail } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

const QUIZ: QuizDetail = {
  id: 'quiz.q1',
  kind: 'quiz',
  version: 1,
  language: 'python',
  title: 'Pattern check',
  slug: 'pattern-check',
  difficulty: 'easy',
  concepts: ['patterns.two_pointers'],
  prerequisites: [],
  estimated_time_minutes: 5,
  quiz_type: 'mixed_review',
  questions: [
    {
      id: 'q1',
      prompt: 'Sorted array, pair sum?',
      choices: ['two pointers', 'stack'],
      concepts: [],
    },
    {
      id: 'q2',
      prompt: 'Balanced brackets?',
      choices: ['two pointers', 'stack'],
      concepts: [],
    },
  ],
};

const ANSWERS: Record<string, { correct: boolean; explanation: string }> = {
  q1: { correct: true, explanation: 'Sorted input invites two pointers.' },
  q2: { correct: false, explanation: 'Matching openers and closers is a stack.' },
};

describe('QuizRoute', () => {
  it('walks the questions and shows a summary', async () => {
    const user = userEvent.setup();
    const { calls } = mockApi({
      'GET /api/v1/content/quiz.q1': { json: QUIZ },
      'POST /api/v1/quizzes/answer': (call: RecordedCall) => {
        const body = call.body as { question_id: string };
        const graded = ANSWERS[body.question_id];
        return {
          json: {
            question_id: body.question_id,
            correct: graded.correct,
            explanation: graded.explanation,
            concepts_changed: [],
            next_review_due_at: null,
          },
        };
      },
    });

    renderWithProviders(<App />, { route: '/quiz/quiz.q1' });

    expect(await screen.findByText('Sorted array, pair sum?')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'two pointers' }));
    expect(await screen.findByText('Sorted input invites two pointers.')).toBeInTheDocument();

    const answerCall = calls.find((call) => call.url === '/api/v1/quizzes/answer');
    expect(answerCall?.body).toEqual({
      quiz_id: 'quiz.q1',
      question_id: 'q1',
      choice: 'two pointers',
    });

    await user.click(screen.getByRole('button', { name: /next question/i }));
    expect(await screen.findByText('Balanced brackets?')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'two pointers' }));
    expect(
      await screen.findByText('Matching openers and closers is a stack.'),
    ).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /finish quiz/i }));
    expect(await screen.findByText(/1 \/ 2 correct/i)).toBeInTheDocument();
  });
});
