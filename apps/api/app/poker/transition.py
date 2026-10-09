"""Pure deterministic transitions for beginning a Texas Hold'em hand."""

from collections.abc import Sequence
from dataclasses import replace

from .errors import (
    HandAlreadyActiveError,
    InsufficientPlayersError,
    InvalidBlindsError,
    InvalidDealerError,
    InvalidDeckError,
    InvalidHandIdError,
    InvalidSeatingError,
)
from .model import (
    MAX_SEAT,
    MIN_SEAT,
    ActiveHand,
    Card,
    HandId,
    HandPhase,
    HandPlayer,
    Rank,
    SeatedPlayer,
    Suit,
    TableState,
    standard_deck,
)


def _validate_seating(seats: tuple[SeatedPlayer, ...]) -> None:
    if len(seats) > MAX_SEAT:
        raise InvalidSeatingError("a table cannot contain more than eight seated players")

    for player in seats:
        if type(player.player_id) is not str or not player.player_id.strip():
            raise InvalidSeatingError("player identifiers must be non-blank strings")

    seat_numbers: set[int] = set()
    player_ids: set[str] = set()
    for player in seats:
        if type(player.seat) is not int or not MIN_SEAT <= player.seat <= MAX_SEAT:
            raise InvalidSeatingError("seat numbers must be integers from 1 through 8")
        if player.seat in seat_numbers:
            raise InvalidSeatingError(f"seat {player.seat} is occupied more than once")
        if player.player_id in player_ids:
            raise InvalidSeatingError("a player cannot occupy more than one seat")
        if type(player.stack) is not int or player.stack < 0:
            raise InvalidSeatingError("table stacks must be non-negative integers")
        seat_numbers.add(player.seat)
        player_ids.add(player.player_id)


def _validate_blinds(small_blind: int, big_blind: int) -> None:
    if (
        type(small_blind) is not int
        or type(big_blind) is not int
        or small_blind <= 0
        or small_blind >= big_blind
    ):
        raise InvalidBlindsError("blinds must be positive integers with small blind < big blind")


def _validate_deck(ordered_deck: Sequence[Card]) -> tuple[Card, ...]:
    try:
        deck = tuple(ordered_deck)
    except TypeError as error:
        raise InvalidDeckError("the deck must be an ordered iterable of cards") from error
    if any(
        type(card) is not Card
        or not isinstance(card.rank, Rank)
        or not isinstance(card.suit, Suit)
        for card in deck
    ):
        raise InvalidDeckError("the deck contains an invalid card")
    if len(deck) != 52 or len(set(deck)) != 52 or set(deck) != set(standard_deck()):
        raise InvalidDeckError("the deck must contain every standard card exactly once")
    return deck


def _clockwise_orbit_after(seat: int, active_seats: tuple[int, ...]) -> tuple[int, ...]:
    """Return one full orbit after ``seat``; the reference seat is last."""

    return tuple(
        sorted(
            active_seats,
            key=lambda candidate: (candidate - seat - 1) % MAX_SEAT,
        )
    )


def start_hand(
    table: TableState,
    *,
    hand_id: HandId,
    dealer_seat: int,
    small_blind: int,
    big_blind: int,
    ordered_deck: Sequence[Card],
) -> TableState:
    """Return a new table with one deterministic hand in the preflop phase.

    The first element of ``ordered_deck`` is dealt first. Cards are dealt one at a
    time clockwise, starting after the dealer, for two complete rounds.
    """

    if table.active_hand is not None:
        raise HandAlreadyActiveError("a hand is already active")

    _validate_seating(table.seats)
    _validate_blinds(small_blind, big_blind)
    deck = _validate_deck(ordered_deck)

    if type(hand_id) is not str or not hand_id.strip():
        raise InvalidHandIdError("hand identifiers must be non-blank strings")
    if type(dealer_seat) is not int or not MIN_SEAT <= dealer_seat <= MAX_SEAT:
        raise InvalidDealerError("the dealer seat must be an integer from 1 through 8")

    active = tuple(player for player in table.seats if player.stack > 0)
    if len(active) < 2:
        raise InsufficientPlayersError("at least two players with chips are required")
    if len(active) > MAX_SEAT:
        raise InvalidSeatingError("a hand cannot contain more than eight active players")

    active_seats = tuple(player.seat for player in active)
    if dealer_seat not in active_seats:
        raise InvalidDealerError("the dealer seat must belong to an active player")

    after_dealer = _clockwise_orbit_after(dealer_seat, active_seats)
    if len(active) == 2:
        small_blind_seat = dealer_seat
        big_blind_seat = after_dealer[0]
        first_to_act_seat = dealer_seat
    else:
        small_blind_seat = after_dealer[0]
        big_blind_seat = after_dealer[1]
        first_to_act_seat = after_dealer[2]

    contributions = {player.seat: 0 for player in active}
    updated_by_seat = {player.seat: player for player in table.seats}
    for blind_seat, required in (
        (small_blind_seat, small_blind),
        (big_blind_seat, big_blind),
    ):
        player = updated_by_seat[blind_seat]
        posted = min(player.stack, required)
        updated_by_seat[blind_seat] = replace(player, stack=player.stack - posted)
        contributions[blind_seat] += posted

    cards_by_seat: dict[int, list[Card]] = {seat: [] for seat in active_seats}
    deal_order = after_dealer
    dealt = 0
    for _round in range(2):
        for seat in deal_order:
            cards_by_seat[seat].append(deck[dealt])
            dealt += 1

    hand_players = tuple(
        HandPlayer(
            player_id=player.player_id,
            seat=player.seat,
            contribution=contributions[player.seat],
            hole_cards=(cards_by_seat[player.seat][0], cards_by_seat[player.seat][1]),
        )
        for player in sorted(active, key=lambda item: item.seat)
    )
    pot = sum(player.contribution for player in hand_players)
    hand = ActiveHand(
        hand_id=hand_id,
        phase=HandPhase.PREFLOP,
        players=hand_players,
        dealer_seat=dealer_seat,
        small_blind_seat=small_blind_seat,
        big_blind_seat=big_blind_seat,
        first_to_act_seat=first_to_act_seat,
        pot=pot,
        remaining_deck=deck[dealt:],
    )
    updated_seats = tuple(updated_by_seat[player.seat] for player in table.seats)
    return TableState(seats=updated_seats, active_hand=hand)
