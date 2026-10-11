import { Component, input } from '@angular/core';
import { PlayingCardComponent } from '../playing-card/playing-card.component';
import { TableSeat } from '../table-view.model';
@Component({ selector: 'app-player-seat', imports: [PlayingCardComponent], templateUrl: './player-seat.component.html', styleUrl: './player-seat.component.scss' })
export class PlayerSeatComponent {
  readonly seat = input.required<TableSeat>();
  readonly isHero = input(false);
  protected isCurrentTurn(seat: TableSeat): boolean { return seat.status === 'occupied' && seat.isCurrentTurn; }
}
