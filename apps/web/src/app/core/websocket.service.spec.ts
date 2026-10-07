import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WebsocketService } from './websocket.service';

class FakeWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readonly url: string;
  readyState = FakeWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  open(): void {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  close(): void {
    this.readyState = FakeWebSocket.CLOSING;
  }
}

describe('WebsocketService', () => {
  let service: WebsocketService;

  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    TestBed.configureTestingModule({});
    service = TestBed.inject(WebsocketService);
  });

  afterEach(() => {
    service.ngOnDestroy();
    vi.unstubAllGlobals();
  });

  it('moves from connecting to connected for the active socket', () => {
    service.connect();
    expect(service.state()).toBe('connecting');
    FakeWebSocket.instances[0].open();
    expect(service.state()).toBe('connected');
  });

  it('disconnects and closes the active socket', () => {
    service.connect();
    const socket = FakeWebSocket.instances[0];
    socket.open();
    service.disconnect();
    expect(socket.readyState).toBe(FakeWebSocket.CLOSING);
    expect(service.state()).toBe('disconnected');
  });

  it('replaces the previous socket when connecting again', () => {
    service.connect();
    const previous = FakeWebSocket.instances[0];
    service.connect();
    expect(previous.readyState).toBe(FakeWebSocket.CLOSING);
    expect(FakeWebSocket.instances).toHaveLength(2);
    expect(service.state()).toBe('connecting');
  });

  it('ignores a delayed close from the previous socket', () => {
    service.connect();
    const previous = FakeWebSocket.instances[0];
    const delayedClose = previous.onclose;
    service.connect();
    const current = FakeWebSocket.instances[1];
    current.open();
    delayedClose?.(new CloseEvent('close'));
    expect(service.state()).toBe('connected');
    current.onerror?.(new Event('error'));
    expect(service.state()).toBe('error');
  });

  it('ignores a delayed error from the previous socket', () => {
    service.connect();
    const previous = FakeWebSocket.instances[0];
    const delayedError = previous.onerror;
    service.connect();
    FakeWebSocket.instances[1].open();
    delayedError?.(new Event('error'));
    expect(service.state()).toBe('connected');
  });
});
