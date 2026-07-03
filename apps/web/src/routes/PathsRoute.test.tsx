import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import type { PathSummary } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

const SUMMARIES: PathSummary[] = [
  {
    id: 'path.career.python_interview_prep',
    path_type: 'career',
    level: 'beginner',
    title: 'Python Interview Prep',
    slug: 'python-interview-prep',
    description: 'The full arc.',
    outcomes: ['Recognize patterns before coding'],
    assumed_concepts: [],
    estimated_hours: 41,
    units: 13,
    items: 400,
    enrolled: false,
    percent_complete: 0,
  },
  {
    id: 'path.skill.python_foundations',
    path_type: 'skill',
    level: 'intermediate',
    title: 'Python Foundations',
    slug: 'python-foundations',
    description: 'The ground floor.',
    outcomes: ['Use variables and conditionals'],
    assumed_concepts: ['Loops', 'Functions'],
    estimated_hours: 9,
    units: 2,
    items: 56,
    enrolled: true,
    percent_complete: 25,
  },
];

describe('PathsRoute', () => {
  it('lists paths and enrolls from a card', async () => {
    const user = userEvent.setup();
    const { calls } = mockApi({
      'GET /api/v1/paths': { json: SUMMARIES },
      'POST /api/v1/paths/path.career.python_interview_prep/enroll': {
        json: { path_id: 'path.career.python_interview_prep', enrolled: true },
      },
    });

    renderWithProviders(<App />, { route: '/paths' });

    expect(await screen.findByText('Python Interview Prep')).toBeInTheDocument();
    expect(screen.getByText('Python Foundations')).toBeInTheDocument();
    expect(screen.getByText('Career path · beginner · 13 units · ~41h')).toBeInTheDocument();
    expect(screen.getByText(/25% complete/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^enroll$/i }));
    const enrollCall = calls.find((call) => call.url.endsWith('/enroll'));
    expect(enrollCall).toMatchObject({
      method: 'POST',
      url: '/api/v1/paths/path.career.python_interview_prep/enroll',
    });
  });

  it('filters the catalog by competence level', async () => {
    const user = userEvent.setup();
    mockApi({ 'GET /api/v1/paths': { json: SUMMARIES } });

    renderWithProviders(<App />, { route: '/paths' });

    expect(await screen.findByText('Python Interview Prep')).toBeInTheDocument();
    expect(screen.getByText('Python Foundations')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'beginner' }));
    expect(screen.getByText('Python Interview Prep')).toBeInTheDocument();
    expect(screen.queryByText('Python Foundations')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'intermediate' }));
    expect(screen.queryByText('Python Interview Prep')).not.toBeInTheDocument();
    expect(screen.getByText('Python Foundations')).toBeInTheDocument();
  });
});
