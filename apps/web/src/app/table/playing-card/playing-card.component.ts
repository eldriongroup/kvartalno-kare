import { Component, input } from '@angular/core';
import { VisibleCard } from '../table-view.model';
const SUIT_SYMBOLS = { clubs: '♣', diamonds: '♦', hearts: '♥', spades: '♠' } as const;
const SHORT_RANKS = { Jack: 'J', Queen: 'Q', King: 'K', Ace: 'A' } as const;
@Component({ selector: 'app-playing-card', templateUrl: './playing-card.component.html', styleUrl: './playing-card.component.scss' })
export class PlayingCardComponent {
  readonly card = input<VisibleCard>(); readonly hidden = input(false);
  protected symbol(card: VisibleCard): string { return SUIT_SYMBOLS[card.suit]; }
  protected shortRank(card: VisibleCard): string { return SHORT_RANKS[card.rank as keyof typeof SHORT_RANKS] ?? card.rank; }
}
