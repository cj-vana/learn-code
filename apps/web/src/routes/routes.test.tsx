import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { App } from '../App';
import { mockApi, renderWithProviders } from '../test/utils';
import {
  contentDetailFixture,
  contentListFixture,
  planFixture,
  progressFixture,
} from '../test/fixtures';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('routes render', () => {
  it('renders the Learn bench with the adaptive plan', async () => {
    mockApi({
      'GET /api/v1/plan': { json: planFixture },
      'GET /api/v1/progress': { json: progressFixture },
    });

    renderWithProviders(<App />, { route: '/learn' });

    expect(await screen.findByText("Set out the day's work")).toBeInTheDocument();
    expect(await screen.findAllByText('Two Sum')).not.toHaveLength(0);
  });

  it('renders the Playground bench', () => {
    mockApi();
    renderWithProviders(<App />, { route: '/playground' });
    expect(screen.getByText('Try things out loud')).toBeInTheDocument();
    expect(screen.getByLabelText('Standard input')).toBeInTheDocument();
  });

  it('renders the Review lab', async () => {
    mockApi({ 'GET /api/v1/progress': { json: progressFixture } });
    renderWithProviders(<App />, { route: '/review' });
    expect(screen.getByText('Work the errors back down')).toBeInTheDocument();
    expect(await screen.findByText('Off By One')).toBeInTheDocument();
  });

  it('renders the Library atlas grouped by difficulty', async () => {
    mockApi({ 'GET /api/v1/content': { json: contentListFixture } });
    renderWithProviders(<App />, { route: '/library' });
    expect(screen.getByText('The whole catalogue on one shelf')).toBeInTheDocument();
    expect(await screen.findByText('easy')).toBeInTheDocument();
  });

  it('renders the exercise Solve bench', async () => {
    mockApi({ 'GET /api/v1/content/two-sum': { json: contentDetailFixture } });
    renderWithProviders(<App />, { route: '/exercise/two-sum' });
    expect(await screen.findByText('Predict the pattern')).toBeInTheDocument();
    expect(
      await screen.findByText(/Return indices of the two numbers/),
    ).toBeInTheDocument();
  });

  it('redirects the index route to the Learn bench', async () => {
    mockApi({
      'GET /api/v1/plan': { json: planFixture },
      'GET /api/v1/progress': { json: progressFixture },
    });
    renderWithProviders(<App />, { route: '/' });
    expect(await screen.findByText("Set out the day's work")).toBeInTheDocument();
  });
});

describe('progress labels', () => {
  it('renders streak, mastery labels, and the next action', async () => {
    mockApi({ 'GET /api/v1/progress': { json: progressFixture } });

    renderWithProviders(<App />, { route: '/progress' });

    expect(await screen.findByText('day streak')).toBeInTheDocument();
    expect(screen.getByText('Practicing')).toBeInTheDocument();
    expect(screen.getByText('Review ready')).toBeInTheDocument();
    expect(screen.getByText(/Drill hash-map lookups/)).toBeInTheDocument();
    // Concept ids are humanized into readable labels in the meter.
    expect(screen.getAllByText('Hash Map').length).toBeGreaterThan(0);
    expect(screen.getByLabelText('Hash Map mastery')).toBeInTheDocument();
  });
});
