import { Injectable, OnDestroy, signal } from '@angular/core';

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface ConnectionReadyEvent {
  version: 1;
  type: 'connection.ready';
  payload: Record<string, never>;
}

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {
  readonly state = signal<ConnectionState>('disconnected');
  private socket?: WebSocket;

  connect(): void {
    this.disconnect();
    this.state.set('connecting');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${protocol}//${location.host}/ws`);
    this.socket = socket;
    socket.onopen = () => {
      if (this.socket === socket) this.state.set('connected');
    };
    socket.onerror = () => {
      if (this.socket === socket) this.state.set('error');
    };
    socket.onclose = () => {
      if (this.socket !== socket) return;
      this.socket = undefined;
      if (this.state() !== 'error') this.state.set('disconnected');
    };
  }

  disconnect(): void {
    const socket = this.socket;
    this.socket = undefined;
    if (socket) {
      socket.onopen = null;
      socket.onerror = null;
      socket.onclose = null;
      if (socket.readyState < WebSocket.CLOSING) socket.close();
    }
    this.state.set('disconnected');
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
