import type { ReactElement } from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';

/** A recorded fetch call, so tests can assert on method/url/body. */
export interface RecordedCall {
  url: string;
  method: string;
  body: unknown;
}

export interface RouteReply {
  status?: number;
  json?: unknown;
  text?: string;
}

type RouteHandler = RouteReply | ((call: RecordedCall) => RouteReply);
export type RouteMap = Record<string, RouteHandler>;

const DEFAULT_ROUTES: RouteMap = {
  'GET /api/v1/health': { json: { status: 'ok' } },
};

/**
 * Replace global fetch with a router keyed by "METHOD /path". Longer path keys
 * win so `/content/:id` beats `/content`. Returns the recorded calls so a test
 * can assert the client hit `/api/v1` with the right body.
 */
export function mockApi(routes: RouteMap = {}) {
  const table = { ...DEFAULT_ROUTES, ...routes };
  const keys = Object.keys(table).sort((a, b) => b.length - a.length);
  const calls: RecordedCall[] = [];

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString();
    const method = (init?.method ?? 'GET').toUpperCase();
    const body = init?.body ? JSON.parse(init.body as string) : undefined;
    const call: RecordedCall = { url, method, body };
    calls.push(call);

    const matchKey = keys.find((key) => {
      const [keyMethod, keyPath] = key.split(' ');
      return keyMethod === method && url.startsWith(keyPath);
    });

    if (!matchKey) {
      return new Response(
        JSON.stringify({
          error: { code: 'internal_error', message: `no stub for ${method} ${url}`, details: {} },
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } },
      );
    }

    const handler = table[matchKey];
    const reply = typeof handler === 'function' ? handler(call) : handler;
    const status = reply.status ?? 200;
    const payload = reply.text ?? (reply.json === undefined ? '' : JSON.stringify(reply.json));
    return new Response(payload, {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });

  vi.stubGlobal('fetch', fetchMock);
  return { calls, fetchMock };
}

export function renderWithProviders(ui: ReactElement, { route = '/' }: { route?: string } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
