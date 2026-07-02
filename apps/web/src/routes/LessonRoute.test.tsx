import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import type { LessonDetail } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

const LESSON: LessonDetail = {
  id: 'lesson.l1',
  kind: 'lesson',
  version: 1,
  language: 'python',
  title: 'Two pointers, gently',
  slug: 'two-pointers-gently',
  difficulty: 'easy',
  concepts: ['patterns.two_pointers'],
  prerequisites: [],
  estimated_time_minutes: 10,
  body_markdown: 'Move both ends toward the middle.',
  checkpoints: [
    {
      question: 'Why move the left pointer?',
      answer: 'To shrink the window.',
      explanation: 'Because the window is too wide.',
    },
  ],
};

describe('LessonRoute', () => {
  it('renders the lesson, reveals a checkpoint, and completes', async () => {
    const user = userEvent.setup();
    const { calls } = mockApi({
      'GET /api/v1/content/lesson.l1': { json: LESSON },
      'POST /api/v1/lessons/lesson.l1/complete': {
        json: { lesson_id: 'lesson.l1', completed_at: '2026-07-02T12:00:00Z' },
      },
    });

    renderWithProviders(<App />, { route: '/lesson/lesson.l1' });

    expect(await screen.findByText('Move both ends toward the middle.')).toBeInTheDocument();
    expect(screen.queryByText('To shrink the window.')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /reveal the answer/i }));
    expect(screen.getByText('To shrink the window.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /mark lesson complete/i }));
    expect(await screen.findByText(/lesson filed/i)).toBeInTheDocument();

    const completion = calls.find((call) => call.url.endsWith('/complete'));
    expect(completion).toMatchObject({
      method: 'POST',
      url: '/api/v1/lessons/lesson.l1/complete',
    });
  });
});
