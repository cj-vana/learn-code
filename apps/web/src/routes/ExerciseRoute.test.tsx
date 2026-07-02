import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders, type RecordedCall } from '../test/utils';
import { contentDetailFixture, submissionFixture } from '../test/fixtures';

afterEach(() => {
  vi.unstubAllGlobals();
});

async function loadSolveBench(extraRoutes = {}) {
  const api = mockApi({
    'GET /api/v1/content/two-sum': { json: contentDetailFixture },
    'POST /api/v1/exercises/submit': { json: submissionFixture },
    ...extraRoutes,
  });
  renderWithProviders(<App />, { route: '/exercise/two-sum' });
  await screen.findByText('Predict the pattern');
  return api;
}

function submitBody(calls: RecordedCall[]) {
  const call = calls.find((entry) => entry.url === '/api/v1/exercises/submit');
  expect(call, 'a submit call was recorded').toBeTruthy();
  return call!.body as Record<string, unknown>;
}

describe('ExerciseRoute submit flow', () => {
  it('sends the predicted pattern, confidence, and source to /exercises/submit', async () => {
    const user = userEvent.setup();
    const { calls } = await loadSolveBench();

    const prediction = screen.getByRole('group', { name: 'Predicted pattern' });
    await user.click(within(prediction).getByRole('button', { name: 'Hash Map' }));
    await user.click(screen.getByRole('radio', { name: '4' }));

    await user.click(screen.getByRole('button', { name: 'Submit for grading' }));

    await screen.findByText('ALL TESTS PASS');

    const body = submitBody(calls);
    expect(body.predicted_pattern).toBe('hash_map');
    expect(body.confidence).toBe(4);
    expect(body.source).toContain('def two_sum');
    expect(body.content_version).toBe(contentDetailFixture.version);
    expect(body.language).toBe('python');
  });

  it('keeps the submission verdict when a mentor review is unavailable', async () => {
    const user = userEvent.setup();
    await loadSolveBench({
      'POST /api/v1/reviews': {
        status: 503,
        json: {
          error: { code: 'ollama_unavailable', message: 'Ollama is offline', details: {} },
        },
      },
    });

    await user.click(screen.getByRole('button', { name: 'Submit for grading' }));
    expect(await screen.findByText('ALL TESTS PASS')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Request a mentor review' }));

    // The review failure surfaces as a non-blocking note...
    expect(
      await screen.findByText(/Review unavailable right now/),
    ).toBeInTheDocument();
    // ...and the graded verdict is still on the bench.
    expect(screen.getByText('ALL TESTS PASS')).toBeInTheDocument();
  });

  it('reports an available review without disturbing the run status', async () => {
    const user = userEvent.setup();
    await loadSolveBench({
      'POST /api/v1/reviews': {
        json: {
          status: 'unavailable',
          summary: 'Ollama is not reachable. Tests still decide pass/fail.',
          correctness_notes: [],
          readability_notes: [],
          python_simplifications: [],
          big_o_notes: null,
          next_improvement: null,
          encouragement: null,
          solution_disclosed: false,
        },
      },
    });

    await user.click(screen.getByRole('button', { name: 'Submit for grading' }));
    await screen.findByText('ALL TESTS PASS');

    await user.click(screen.getByRole('button', { name: 'Request a mentor review' }));

    await waitFor(() =>
      expect(screen.getByText(/Reviewer unavailable/)).toBeInTheDocument(),
    );
    expect(screen.getByText('ALL TESTS PASS')).toBeInTheDocument();
  });
});
