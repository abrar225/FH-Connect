import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useDraftStore, DraftStore } from '../store/draftStore';

describe('draftStore', () => {
  let store: DraftStore;

  beforeEach(() => {
    store = useDraftStore.getState();
    useDraftStore.setState({
      room: null,
      wsConnected: false,
      transcriptions: [],
      drafts: [],
      insights: null,
      chatMessages: [],
      reportStatus: null,
      isSummaryActive: false,
      isReportActive: false,
    });
  });

  it('should have correct initial state', () => {
    expect(store.room).toBeNull();
    expect(store.wsConnected).toBe(false);
    expect(store.transcriptions).toEqual([]);
    expect(store.drafts).toEqual([]);
  });

  it('should set room correctly', () => {
    const testRoom = 'test-room-123';
    useDraftStore.getState().setRoom(testRoom);
    
    expect(useDraftStore.getState().room).toBe(testRoom);
  });

  it('should add transcriptions', () => {
    const transcription = {
      id: '1',
      text: 'Hello world',
      speaker: 'Test User',
      timestamp: new Date().toISOString(),
    };
    useDraftStore.getState().addTranscription(transcription);
    
    expect(useDraftStore.getState().transcriptions).toHaveLength(1);
    expect(useDraftStore.getState().transcriptions[0].text).toBe('Hello world');
  });

  it('should add chat messages', () => {
    const message = {
      id: 'chat-1',
      senderId: 'user-1',
      senderName: 'User 1',
      text: 'Test message',
      timestamp: new Date().toISOString(),
    };
    useDraftStore.getState().addChatMessage(message);
    
    expect(useDraftStore.getState().chatMessages).toHaveLength(1);
    expect(useDraftStore.getState().chatMessages[0].text).toBe('Test message');
  });

  it('should clear room state on exitRoom', () => {
    useDraftStore.getState().setRoom('test-room');
    useDraftStore.getState().setWsConnected(true);
    useDraftStore.getState().addTranscription({
      id: '1',
      text: 'Test',
      speaker: 'User',
      timestamp: new Date().toISOString(),
    });
    
    useDraftStore.getState().exitRoom();
    
    const state = useDraftStore.getState();
    expect(state.room).toBeNull();
    expect(state.wsConnected).toBe(false);
    expect(state.transcriptions).toEqual([]);
  });

  it('should update report status', () => {
    const status = { ok: true, label: 'processing', detail: 'Generating report...' };
    useDraftStore.getState().setReportStatus(status);
    
    expect(useDraftStore.getState().reportStatus).toEqual(status);
  });
});