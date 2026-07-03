import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import type { PathSummary } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

const SUMMARIES: PathSummary[] = [
  {
    id: 'path.skill.python_foundations',
    path_type: 'skill',
    title: 'Python Foundations',
    slug: 'python-foundations',
    description: 'The ground floor.',
    outcomes: ['Use variables and conditionals'],
    assumed_concepts: [],
    estimated_hours: 9,
    units: 2,
    items: 56,
    enrolled: false,
    percent_complete: 0,
  },
  {
    id: 'path.skill.text_data_collections',
    path_type: 'skill',
    title: 'Text, Data & Collections',
    slug: 'text-data-and-collections',
    description: 'Regex and records.',
    outcomes: ['Extract structured text'],
    assumed_concepts: ['Functions'],
    estimated_hours: 12,
    units: 3,
    items: 80,
    enrolled: false,
    percent_complete: 0,
  },
];

describe('StartRoute', () => {
  it('recommends Foundations to a brand-new learner, more once concepts are ticked', async () => {
    const user = userEvent.setup();
    mockApi({ 'GET /api/v1/paths': { json: SUMMARIES } });

    renderWithProviders(<App />, { route: '/start' });

    const startPanel = (await screen.findByText('Start here')).closest('section') ?? document.body;
    expect(within(startPanel as HTMLElement).getByText('Python Foundations')).toBeInTheDocument();
    expect(screen.getByText('Almost within reach')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Functions' }));

    const updatedPanel = (await screen.findByText('Start here')).closest('section') ?? document.body;
    expect(
      within(updatedPanel as HTMLElement).getByText('Text, Data & Collections'),
    ).toBeInTheDocument();
    expect(screen.queryByText('Almost within reach')).not.toBeInTheDocument();
  });
});
