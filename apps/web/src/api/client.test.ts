import { afterEach, describe, expect, it, vi } from 'vitest';
import { API_BASE, ApiConnectionError, ApiError, apiClient } from './client';
import { mockApi } from '../test/utils';
import { planFixture } from '../test/fixtures';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('apiClient', () => {
  it('targets the relative /api/v1 surface', () => {
    expect(API_BASE).toBe('/api/v1');
  });

  it('requests plan from /api/v1/plan (never a hardcoded host)', async () => {
    const { calls } = mockApi({ 'GET /api/v1/plan': { json: planFixture } });

    const plan = await apiClient.getPlan();

    expect(plan).toHaveLength(2);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe('/api/v1/plan');
    expect(calls[0].url.startsWith('/api/v1/')).toBe(true);
    expect(calls[0].url).not.toMatch(/^https?:\/\//);
  });

  it('sends the submission body as JSON to /api/v1/exercises/submit', async () => {
    const { calls } = mockApi({
      'POST /api/v1/exercises/submit': {
        json: {
          submission_id: 's1',
          run: {
            status: 'passed',
            passed: 1,
            failed: 0,
            stdout: '',
            stderr: '',
            duration_ms: 1,
            test_summary: [],
          },
          progress_delta: {
            concepts_changed: [],
            mastery_before: 0,
            mastery_after: 1,
            review_due_at: null,
          },
          next_actions: [],
        },
      },
    });

    await apiClient.submitExercise({
      exercise_id: 'two-sum',
      content_version: 3,
      language: 'python',
      source: 'print(1)',
      predicted_pattern: 'hash_map',
      confidence: 4,
    });

    expect(calls[0].method).toBe('POST');
    expect(calls[0].url).toBe('/api/v1/exercises/submit');
    expect(calls[0].body).toMatchObject({
      exercise_id: 'two-sum',
      predicted_pattern: 'hash_map',
      confidence: 4,
      source: 'print(1)',
    });
  });

  it('unwraps the error envelope into an ApiError', async () => {
    mockApi({
      'GET /api/v1/content/missing': {
        status: 404,
        json: { error: { code: 'content_not_found', message: 'No such exercise', details: {} } },
      },
    });

    await expect(apiClient.getContent('missing')).rejects.toMatchObject({
      name: 'ApiError',
      code: 'content_not_found',
      status: 404,
      message: 'No such exercise',
    });
  });

  it('maps a transport failure to ApiConnectionError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('network down'))),
    );

    await expect(apiClient.getPlan()).rejects.toBeInstanceOf(ApiConnectionError);
  });

  it('exposes ApiError as an Error subclass', () => {
    expect(new ApiError('internal_error', 'boom', 500)).toBeInstanceOf(Error);
  });
});
