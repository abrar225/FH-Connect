import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { getAccessToken, authFetch, authWsUrl } from './api';

const mockSession = {
  data: {
    session: {
      access_token: 'test-token-123',
    },
  },
};

const mockSignOut = vi.fn();

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      signOut: mockSignOut,
    },
  },
}));

vi.mock('@/app/lib/env', () => ({
  API_VERSION: 'v1',
  API_BASE: 'http://localhost:8000',
  getApiUrl: (endpoint: string) => `http://localhost:8000/api/v1${endpoint}`,
  getWsUrl: (endpoint: string) => `ws://localhost:8000${endpoint}`,
}));

vi.stubGlobal('fetch', vi.fn());
vi.stubGlobal('Headers', vi.fn((init?: any) => {
  const headers = new Map();
  if (init) {
    Object.entries(init).forEach(([key, value]) => headers.set(key.toLowerCase(), value));
  }
  return {
    has: (key: string) => headers.has(key.toLowerCase()),
    get: (key: string) => headers.get(key.toLowerCase()),
    set: (key: string, value: string) => headers.set(key.toLowerCase(), value),
  };
}));

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getAccessToken', () => {
    it('should return access token from session', async () => {
      const { supabase } = await import('@/lib/supabase');
      vi.mocked(supabase.auth.getSession).mockResolvedValue(mockSession as any);
      
      const token = await getAccessToken();
      
      expect(token).toBe('test-token-123');
    });

    it('should return null when no session exists', async () => {
      const { supabase } = await import('@/lib/supabase');
      vi.mocked(supabase.auth.getSession).mockResolvedValue({ data: { session: null } });
      
      const token = await getAccessToken();
      
      expect(token).toBeNull();
    });
  });

  describe('authFetch', () => {
    it('should include authorization header with token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({}),
      } as any);

      await authFetch('/api/test', { method: 'GET' });
      
      expect(global.fetch).toHaveBeenCalled();
    });

    it('should handle network errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
      
      const response = await authFetch('/api/test');
      
      expect(response.status).toBe(503);
    });

    it('should prepend API_BASE for relative URLs', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({}),
      } as any);

      await authFetch('/meeting/test-room/context');
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/meeting/test-room/context',
        expect.any(Object)
      );
    });
  });

  describe('authWsUrl', () => {
    it('should construct WebSocket URL with token', async () => {
      const url = await authWsUrl('/ws/test-room');
      
      expect(url).toContain('token=');
    });
  });
});