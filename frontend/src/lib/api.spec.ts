import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { apiFetch, revokeSession, saveTokens } from './api';

describe('API session handling', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shares one refresh request across concurrent unauthorized responses', async () => {
    saveTokens('expired-access', 'valid-refresh');
    let refreshCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/auth/refresh')) {
        refreshCalls += 1;
        return new Response(
          JSON.stringify({ accessToken: 'new-access', refreshToken: 'new-refresh' }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }
      const authorized = localStorage.getItem('flowlog_access_token') === 'new-access';
      return new Response(JSON.stringify({ ok: authorized }), {
        status: authorized ? 200 : 401,
        headers: { 'Content-Type': 'application/json' },
      });
    });
    vi.stubGlobal('fetch', fetchMock);

    const results = await Promise.all([
      apiFetch<{ ok: boolean }>('/projects'),
      apiFetch<{ ok: boolean }>('/tasks'),
    ]);

    expect(results).toEqual([{ ok: true }, { ok: true }]);
    expect(refreshCalls).toBe(1);
  });

  it('clears local credentials even when server-side logout fails', async () => {
    saveTokens('access', 'refresh');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    await expect(revokeSession()).rejects.toThrow('offline');
    expect(localStorage.getItem('flowlog_access_token')).toBeNull();
    expect(localStorage.getItem('flowlog_refresh_token')).toBeNull();
  });
});
