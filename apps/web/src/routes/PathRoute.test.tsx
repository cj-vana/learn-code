import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import type { PathDetail } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

const DETAIL: PathDetail = {
  id: 'path.skill.python_foundations',
  path_type: 'skill',
  title: 'Python Foundations',
  slug: 'python-foundations',
  description: 'The ground floor.',
  outcomes: ['Use variables and conditionals'],
  estimated_hours: 9,
  enrolled: true,
  percent_complete: 33,
  units: [
    {
      id: 'unit.python_refresh',
      title: 'Python Refresh',
      description: 'Start here.',
      percent_complete: 50,
      status: 'in_progress',
      milestone: null,
      items: [
        {
          id: 'lesson.library.python_refresh.a01',
          kind: 'lesson',
          title: 'Variables, gently',
          estimated_time_minutes: 8,
          status: 'complete',
        },
        {
          id: 'quiz.library.python_refresh.a01',
          kind: 'quiz',
          title: 'Refresh check',
          estimated_time_minutes: 5,
          status: 'todo',
        },
      ],
    },
  ],
  next_item_id: 'quiz.library.python_refresh.a01',
};

describe('PathRoute', () => {
  it('renders the syllabus with statuses and a Continue link to the next item', async () => {
    mockApi({
      'GET /api/v1/paths/path.skill.python_foundations': { json: DETAIL },
    });

    renderWithProviders(<App />, { route: '/path/path.skill.python_foundations' });

    expect(await screen.findByText('Python Refresh')).toBeInTheDocument();
    expect(screen.getByText('Variables, gently')).toBeInTheDocument();
    expect(screen.getByText('Refresh check')).toBeInTheDocument();

    const continueLink = screen.getByRole('link', { name: /continue/i });
    expect(continueLink).toHaveAttribute(
      'href',
      '/quiz/quiz.library.python_refresh.a01',
    );

    const completedRow = screen.getByText('Variables, gently').closest('li');
    expect(completedRow?.textContent).toMatch(/done/i);
  });
});
