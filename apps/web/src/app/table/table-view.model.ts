export type Suit = 'clubs' | 'diamonds' | 'hearts' | 'spades';
export type Rank = '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10' | 'Jack' | 'Queen' | 'King' | 'Ace';
export interface VisibleCard { readonly rank: Rank; readonly suit: Suit; }
export type HoleCards =
  | { readonly visibility: 'visible'; readonly cards: readonly [VisibleCard, VisibleCard] }
  | { readonly visibility: 'hidden'; readonly count: 0 | 2 };
interface SeatBase { readonly seatNumber: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8; }
export interface AvailableSeat extends SeatBase { readonly status: 'available'; }
export interface OccupiedSeat extends SeatBase {
  readonly status: 'occupied'; readonly playerId: string; readonly displayName: string;
  readonly initials: string; readonly avatarUrl?: string; readonly stack: number;
  readonly currentContribution: number; readonly dealer: boolean; readonly smallBlind: boolean;
  readonly bigBlind: boolean; readonly isCurrentTurn: boolean;
  readonly connection: 'connected' | 'disconnected' | 'inactive'; readonly holeCards: HoleCards;
}
export type TableSeat = AvailableSeat | OccupiedSeat;
export type LegalAction =
  | { readonly type: 'fold'; readonly label: string }
  | { readonly type: 'check'; readonly label: string }
  | { readonly type: 'call'; readonly label: string; readonly amount: number }
  | { readonly type: 'raise'; readonly label: string; readonly amount: number };
export interface TableViewModel {
  readonly tableName: string; readonly handDisplayNumber: string; readonly heroPlayerId: string;
  readonly seats: readonly TableSeat[]; readonly communityCards: readonly VisibleCard[];
  readonly totalPot: number; readonly potBreakdown?: readonly { readonly label: string; readonly amount: number }[];
  readonly heroTurn: { readonly isActive: boolean; readonly notification: string; readonly actions: readonly LegalAction[] };
}
export type VisualSeatPosition = 'bottom-center' | 'bottom-left' | 'left' | 'top-left' | 'top-center' | 'top-right' | 'right' | 'bottom-right';
export interface ProjectedSeat { readonly seat: TableSeat; readonly visualPosition: VisualSeatPosition; }
const VISUAL_POSITIONS: readonly VisualSeatPosition[] = ['bottom-center', 'bottom-left', 'left', 'top-left', 'top-center', 'top-right', 'right', 'bottom-right'];
export function projectSeatsForHero(state: TableViewModel): readonly ProjectedSeat[] {
  const heroIndex = state.seats.findIndex((seat) => seat.status === 'occupied' && seat.playerId === state.heroPlayerId);
  if (heroIndex < 0 || state.seats.length !== 8) throw new Error('The table preview requires eight seats and an occupied hero seat.');
  return state.seats.map((seat, index) => ({ seat, visualPosition: VISUAL_POSITIONS[(index - heroIndex + state.seats.length) % state.seats.length] }));
}
