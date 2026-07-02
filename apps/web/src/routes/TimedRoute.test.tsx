import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import { activeTimedSession, startTimedSession } from '../lib/timedSession';
import type { TimedSessionResponse } from '../contracts';

afterEach(() => {
  vi.unstubAllGlobals();
});

beforeEach(() => {
  sessionStorage.clear();
});

const SESSION: TimedSessionResponse = {
  session_id: 'timed-1',
  minutes_per_problem: 15,
  exercises: [
    {
      id: 'exercise.library.two_pointers.a01',
      title: 'Meet in the middle',
      concepts: ['patterns.two_pointers'],
      estimated_time_minutes: 12,
    },
  ],
};

describe('TimedRoute', () => {
  it('starts a session and navigates to the first problem', async () => {
    const user = userEvent.setup();
    const { calls } = mockApi({
      'POST /api/v1/sessions/timed': { json: SESSION },
      'GET /api/v1/content/exercise.library.two_pointers.a01': {
        status: 404,
        json: { error: { code: 'content_not_found', message: 'nope', details: {} } },
      },
    });

    renderWithProviders(<App />, { route: '/timed' });

    await user.click(await screen.findByRole('button', { name: /start timed session/i }));

    const startCall = calls.find((call) => call.url === '/api/v1/sessions/timed');
    expect(startCall?.body).toMatchObject({ count: 3, minutes_per_problem: 15 });
    expect(activeTimedSession()?.session_id).toBe('timed-1');
  });

  it('shows the session summary with outcomes', async () => {
    mockApi({});
    startTimedSession(SESSION);

    renderWithProviders(<App />, { route: '/timed' });

    expect(await screen.findByText('Meet in the middle')).toBeInTheDocument();
    expect(screen.getByText(/not submitted/i)).toBeInTheDocument();
    expect(screen.getByText(/session in progress/i)).toBeInTheDocument();
  });
});
