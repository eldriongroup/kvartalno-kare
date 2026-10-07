import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HealthService } from '../core/health.service';
import { WebsocketService } from '../core/websocket.service';

@Component({
  selector: 'app-lobby',
  imports: [RouterLink],
  templateUrl: './lobby.component.html',
  styleUrl: './lobby.component.scss',
})
export class LobbyComponent implements OnInit, OnDestroy {
  protected readonly health = inject(HealthService);
  protected readonly websocket = inject(WebsocketService);

  ngOnInit(): void {
    this.health.check();
    this.websocket.connect();
  }

  ngOnDestroy(): void {
    this.websocket.disconnect();
  }
}
