import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { HealthService } from '../core/health.service';
import { WebsocketService } from '../core/websocket.service';
import { LobbyComponent } from './lobby.component';

describe('LobbyComponent', () => {
  let fixture: ComponentFixture<LobbyComponent>;
  const health = { state: signal<'healthy'>('healthy'), check: vi.fn() };
  const websocket = {
    state: signal<'connected'>('connected'),
    connect: vi.fn(),
    disconnect: vi.fn(),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [LobbyComponent],
      providers: [
        provideRouter([]),
        { provide: HealthService, useValue: health },
        { provide: WebsocketService, useValue: websocket },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LobbyComponent);
    fixture.detectChanges();
  });

  it('checks both services and renders their state', () => {
    expect(health.check).toHaveBeenCalledOnce();
    expect(websocket.connect).toHaveBeenCalledOnce();
    expect(fixture.nativeElement.textContent).toContain('healthy');
    expect(fixture.nativeElement.textContent).toContain('connected');
  });

  it('disconnects the socket when destroyed', () => {
    fixture.destroy();
    expect(websocket.disconnect).toHaveBeenCalledOnce();
  });
});
