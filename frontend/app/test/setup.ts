import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});

const mockRef = {
  current: null,
};

const mockTrackRef = {
  participant: {
    identity: 'test-user',
    name: 'Test User',
  },
  publication: {
    trackSid: 'test-track-sid',
    kind: 'audio',
  },
};

const mockTranscript = {
  id: '1',
  text: 'Test transcript',
  timestamp: new Date().toISOString(),
  speaker: 'Test User',
};

vi.stubGlobal('IntersectionObserver', vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
})));

vi.stubGlobal('ResizeObserver', vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
})));

export { mockRef, mockTrackRef, mockTranscript };