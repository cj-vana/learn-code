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
  body_markdown: [
    'In Python a *variable* points at a value. Bind it with `score = 10`.',
    '',
    '```python',
    'def add(a, b):',
    '    return a + b',
    '```',
  ].join('\n'),
  checkpoints: [
    {
      question: 'Why move the `left` pointer?',
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

    expect(await screen.findByText(/points at a value/i)).toBeInTheDocument();
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

  it('renders markdown prose and highlighted code instead of literal source', async () => {
    mockApi({ 'GET /api/v1/content/lesson.l1': { json: LESSON } });

    const { container } = renderWithProviders(<App />, { route: '/lesson/lesson.l1' });
    await screen.findByText(/points at a value/i);

    // Emphasis becomes an <em>, not literal asterisks.
    expect(screen.getByText('variable').tagName).toBe('EM');

    // Inline code becomes a chip, not literal backticks.
    const inline = screen.getByText('score = 10');
    expect(inline.tagName).toBe('CODE');
    expect(inline).toHaveClass('tok-inline');

    // A fenced block becomes a real <pre><code> with syntax-highlighted tokens.
    const pre = container.querySelector('pre');
    expect(pre).not.toBeNull();
    expect(pre?.querySelector('code')).not.toBeNull();
    expect(container.querySelector('.tok-keyword')?.textContent).toBe('def');

    // No raw markdown leaks through anywhere on the page.
    expect(container.textContent).not.toContain('```');
    expect(container.textContent).not.toContain('*variable*');
    expect(container.textContent).not.toContain('`score = 10`');
  });
});
