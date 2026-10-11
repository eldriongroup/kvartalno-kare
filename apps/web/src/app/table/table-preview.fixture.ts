import { TableViewModel } from './table-view.model';
export const TABLE_PREVIEW: TableViewModel = {
  tableName: 'The Neighbourhood Table', handDisplayNumber: '#0042', heroPlayerId: 'player-mira',
  seats: [
    { status: 'occupied', seatNumber: 1, playerId: 'player-boris', displayName: 'Boris', initials: 'BO', stack: 1840, currentContribution: 20, dealer: false, smallBlind: true, bigBlind: false, isCurrentTurn: false, connection: 'connected', holeCards: { visibility: 'hidden', count: 2 } },
    { status: 'available', seatNumber: 2 },
    { status: 'occupied', seatNumber: 3, playerId: 'player-kaloyan', displayName: 'Kaloyan', initials: 'KA', stack: 2460, currentContribution: 40, dealer: false, smallBlind: false, bigBlind: true, isCurrentTurn: false, connection: 'connected', holeCards: { visibility: 'hidden', count: 2 } },
    { status: 'occupied', seatNumber: 4, playerId: 'player-iva', displayName: 'Iva', initials: 'IV', stack: 965, currentContribution: 0, dealer: false, smallBlind: false, bigBlind: false, isCurrentTurn: false, connection: 'inactive', holeCards: { visibility: 'hidden', count: 0 } },
    { status: 'available', seatNumber: 5 },
    { status: 'occupied', seatNumber: 6, playerId: 'player-stefan', displayName: 'Stefan', initials: 'ST', stack: 3210, currentContribution: 40, dealer: true, smallBlind: false, bigBlind: false, isCurrentTurn: false, connection: 'connected', holeCards: { visibility: 'hidden', count: 2 } },
    { status: 'available', seatNumber: 7 },
    { status: 'occupied', seatNumber: 8, playerId: 'player-mira', displayName: 'Mira', initials: 'MI', stack: 2780, currentContribution: 40, dealer: false, smallBlind: false, bigBlind: false, isCurrentTurn: true, connection: 'connected', holeCards: { visibility: 'visible', cards: [{ rank: 'Ace', suit: 'spades' }, { rank: 'Queen', suit: 'hearts' }] } },
  ],
  communityCards: [{ rank: '10', suit: 'hearts' }, { rank: 'Jack', suit: 'clubs' }, { rank: '4', suit: 'spades' }],
  totalPot: 180, potBreakdown: [{ label: 'Main pot', amount: 180 }],
  heroTurn: { isActive: true, notification: 'Your turn', actions: [{ type: 'fold', label: 'Fold' }, { type: 'call', label: 'Call 20', amount: 20 }, { type: 'raise', label: 'Raise to 80', amount: 80 }] },
};
