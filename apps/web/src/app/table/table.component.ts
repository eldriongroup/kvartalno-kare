import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ActionPanelComponent } from './action-panel/action-panel.component';
import { PlayerSeatComponent } from './player-seat/player-seat.component';
import { PlayingCardComponent } from './playing-card/playing-card.component';
import { TABLE_PREVIEW } from './table-preview.fixture';
import { projectSeatsForHero } from './table-view.model';

@Component({
  selector: 'app-table',
  imports: [RouterLink, ActionPanelComponent, PlayerSeatComponent, PlayingCardComponent],
  templateUrl: './table.component.html',
  styleUrl: './table.component.scss',
})
export class TableComponent {
  readonly state = input(TABLE_PREVIEW);
  protected get table() { return this.state(); }
  protected get projectedSeats() { return projectSeatsForHero(this.table); }
}
