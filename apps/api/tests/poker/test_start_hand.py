from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from app.poker import (
    Card,
    HandAlreadyActiveError,
    HandId,
    HandPhase,
    InsufficientPlayersError,
    InvalidBlindsError,
    InvalidDealerError,
    InvalidDeckError,
    InvalidHandIdError,
    InvalidSeatingError,
    PlayerId,
    SeatedPlayer,
    TableState,
    standard_deck,
    start_hand,
)

DECK = standard_deck()


def player(seat: int, stack: int = 100) -> SeatedPlayer:
    return SeatedPlayer(PlayerId(f"player-{seat}"), seat, stack)


def table(*players: SeatedPlayer) -> TableState:
    return TableState(seats=players)


def begin(
    state: TableState,
    dealer: int,
    *,
    small_blind: int = 5,
    big_blind: int = 10,
    deck: tuple[Card, ...] = DECK,
) -> TableState:
    return start_hand(
        state,
        hand_id=HandId("hand-1"),
        dealer_seat=dealer,
        small_blind=small_blind,
        big_blind=big_blind,
        ordered_deck=deck,
    )


def hand_players_by_seat(result: TableState) -> dict[int, object]:
    assert result.active_hand is not None
    return {participant.seat: participant for participant in result.active_hand.players}


def stacks_by_seat(result: TableState) -> dict[int, int]:
    return {seated.seat: seated.stack for seated in result.seats}


def test_heads_up_start_assigns_roles_posts_blinds_and_deals_clockwise() -> None:
    result = begin(table(player(1), player(6)), dealer=6)
    assert result.active_hand is not None
    hand = result.active_hand
    participants = {participant.seat: participant for participant in hand.players}

    assert (hand.dealer_seat, hand.small_blind_seat, hand.big_blind_seat) == (6, 6, 1)
    assert hand.first_to_act_seat == 6
    assert hand.phase is HandPhase.PREFLOP
    assert hand.pot == 15
    assert stacks_by_seat(result) == {1: 90, 6: 95}
    assert participants[1].contribution == 10
    assert participants[6].contribution == 5
    # The first sequence element is dealt first: seat 1, seat 6, then round two.
    assert participants[1].hole_cards == (DECK[0], DECK[2])
    assert participants[6].hole_cards == (DECK[1], DECK[3])
    assert hand.remaining_deck == DECK[4:]


def test_three_player_roles_and_first_to_act_follow_real_seat_numbers() -> None:
    result = begin(table(player(1), player(4), player(7)), dealer=1)
    assert result.active_hand is not None
    assert (
        result.active_hand.small_blind_seat,
        result.active_hand.big_blind_seat,
        result.active_hand.first_to_act_seat,
    ) == (4, 7, 1)


def test_eight_player_start_assigns_deals_and_wraps_around() -> None:
    result = begin(table(*(player(seat) for seat in range(1, 9))), dealer=7)
    assert result.active_hand is not None
    hand = result.active_hand
    participants = {participant.seat: participant for participant in hand.players}

    assert (hand.small_blind_seat, hand.big_blind_seat, hand.first_to_act_seat) == (8, 1, 2)
    expected_order = (8, 1, 2, 3, 4, 5, 6, 7)
    for index, seat in enumerate(expected_order):
        assert participants[seat].hole_cards == (DECK[index], DECK[index + 8])
    assert hand.remaining_deck == DECK[16:]


def test_gapped_seats_wrap_for_blinds_action_and_dealing() -> None:
    result = begin(table(player(2), player(5), player(8)), dealer=8)
    assert result.active_hand is not None
    hand = result.active_hand
    participants = {participant.seat: participant for participant in hand.players}

    assert (hand.small_blind_seat, hand.big_blind_seat, hand.first_to_act_seat) == (2, 5, 8)
    assert participants[2].hole_cards == (DECK[0], DECK[3])
    assert participants[5].hole_cards == (DECK[1], DECK[4])
    assert participants[8].hole_cards == (DECK[2], DECK[5])


@pytest.mark.parametrize(
    ("short_seat", "stack", "expected_stacks", "expected_contributions"),
    [
        (2, 3, {1: 100, 2: 0, 3: 90}, {1: 0, 2: 3, 3: 10}),
        (3, 7, {1: 100, 2: 95, 3: 0}, {1: 0, 2: 5, 3: 7}),
    ],
)
def test_short_blind_posts_only_available_chips(
    short_seat: int,
    stack: int,
    expected_stacks: dict[int, int],
    expected_contributions: dict[int, int],
) -> None:
    players = tuple(player(seat, stack if seat == short_seat else 100) for seat in (1, 2, 3))
    result = begin(table(*players), dealer=1)
    assert result.active_hand is not None
    assert stacks_by_seat(result) == expected_stacks
    assert {p.seat: p.contribution for p in result.active_hand.players} == expected_contributions
    assert result.active_hand.pot == sum(expected_contributions.values())


def test_zero_stack_player_is_seated_but_inactive_and_receives_no_cards() -> None:
    result = begin(table(player(1), player(2, 0), player(5)), dealer=1)
    assert result.active_hand is not None
    assert {participant.seat for participant in result.active_hand.players} == {1, 5}
    assert stacks_by_seat(result)[2] == 0


def test_cards_are_unique_complete_and_chip_totals_are_conserved() -> None:
    initial = table(player(1, 13), player(3, 4), player(6, 21), player(8, 1))
    result = begin(initial, dealer=6)
    assert result.active_hand is not None
    hand = result.active_hand
    dealt = tuple(card for participant in hand.players for card in participant.hole_cards)

    assert all(len(participant.hole_cards) == 2 for participant in hand.players)
    assert len(dealt) == len(set(dealt)) == 8
    assert len(hand.remaining_deck) == len(set(hand.remaining_deck)) == 44
    assert set(dealt).isdisjoint(hand.remaining_deck)
    assert set(dealt) | set(hand.remaining_deck) == set(DECK)
    assert hand.pot == sum(participant.contribution for participant in hand.players)
    assert sum(seated.stack for seated in result.seats) + hand.pot == sum(
        seated.stack for seated in initial.seats
    )
    assert all(seated.stack >= 0 for seated in result.seats)
    assert all(participant.contribution >= 0 for participant in hand.players)


@pytest.mark.parametrize("players", [(), (player(1),), (player(1, 0), player(2, 0))])
def test_at_least_two_active_players_are_required(players: tuple[SeatedPlayer, ...]) -> None:
    with pytest.raises(InsufficientPlayersError):
        begin(table(*players), dealer=1)


@pytest.mark.parametrize("dealer", [2, 9])
def test_dealer_must_be_an_active_seat(dealer: int) -> None:
    with pytest.raises(InvalidDealerError):
        begin(table(player(1), player(2, 0), player(3)), dealer=dealer)


@pytest.mark.parametrize("seat", [0, 9])
def test_seat_number_must_be_between_one_and_eight(seat: int) -> None:
    with pytest.raises(InvalidSeatingError):
        begin(table(player(seat), player(2)), dealer=2)


def test_more_than_eight_seated_or_active_players_is_rejected() -> None:
    players = tuple(player(seat) for seat in range(1, 10))
    with pytest.raises(InvalidSeatingError, match="more than eight"):
        begin(table(*players), dealer=1)


def test_duplicate_seat_is_rejected() -> None:
    with pytest.raises(InvalidSeatingError, match="occupied more than once"):
        begin(table(player(1), SeatedPlayer(PlayerId("other"), 1, 100)), dealer=1)


def test_duplicate_player_id_is_rejected() -> None:
    duplicate_id = PlayerId("same-player")
    with pytest.raises(InvalidSeatingError, match="more than one seat"):
        begin(
            table(
                SeatedPlayer(duplicate_id, 1, 100),
                SeatedPlayer(duplicate_id, 2, 0),
                player(3),
            ),
            dealer=1,
        )


@pytest.mark.parametrize("player_id", ["", "   ", 1, 1.0, True, [], {}, set()])
def test_invalid_player_id_is_rejected_with_a_domain_error(player_id: object) -> None:
    with pytest.raises(InvalidSeatingError, match="identifiers"):
        begin(
            table(
                SeatedPlayer(cast(Any, player_id), 1, 100),
                player(2),
            ),
            dealer=2,
        )


def test_negative_stack_is_rejected() -> None:
    with pytest.raises(InvalidSeatingError):
        begin(table(player(1, -1), player(2)), dealer=2)


@pytest.mark.parametrize(
    ("small", "big"),
    [(0, 10), (-1, 10), (10, 10), (11, 10), (1.5, 10), (1, True)],
)
def test_invalid_blind_structure_is_rejected(small: object, big: object) -> None:
    with pytest.raises(InvalidBlindsError):
        start_hand(
            table(player(1), player(2)),
            hand_id=HandId("hand-1"),
            dealer_seat=1,
            small_blind=cast(Any, small),
            big_blind=cast(Any, big),
            ordered_deck=DECK,
        )


def test_incomplete_deck_is_rejected() -> None:
    with pytest.raises(InvalidDeckError):
        begin(table(player(1), player(2)), dealer=1, deck=DECK[:-1])


def test_deck_with_an_additional_card_is_rejected() -> None:
    with pytest.raises(InvalidDeckError):
        begin(table(player(1), player(2)), dealer=1, deck=DECK + (DECK[0],))


def test_duplicate_card_deck_is_rejected() -> None:
    duplicate = (DECK[0],) + DECK[:-1]
    with pytest.raises(InvalidDeckError):
        begin(table(player(1), player(2)), dealer=1, deck=duplicate)


def test_card_with_invalid_rank_or_suit_type_is_rejected() -> None:
    invalid = list(DECK)
    invalid[0] = Card(cast(Any, "2"), cast(Any, "clubs"))
    with pytest.raises(InvalidDeckError):
        begin(table(player(1), player(2)), dealer=1, deck=tuple(invalid))


def test_non_card_in_deck_is_rejected() -> None:
    invalid: list[object] = list(DECK)
    invalid[0] = "ace of spaces"
    with pytest.raises(InvalidDeckError):
        start_hand(
            table(player(1), player(2)),
            hand_id=HandId("hand-1"),
            dealer_seat=1,
            small_blind=5,
            big_blind=10,
            ordered_deck=cast(Any, invalid),
        )


def test_non_iterable_deck_is_rejected_with_a_domain_error() -> None:
    for invalid_deck in (None, 52, True, object()):
        with pytest.raises(InvalidDeckError):
            start_hand(
                table(player(1), player(2)),
                hand_id=HandId("hand-1"),
                dealer_seat=1,
                small_blind=5,
                big_blind=10,
                ordered_deck=cast(Any, invalid_deck),
            )


@pytest.mark.parametrize("hand_id", ["", "   ", 1, 1.0, True, [], {}, set()])
def test_invalid_hand_id_is_rejected_with_a_domain_error(hand_id: object) -> None:
    with pytest.raises(InvalidHandIdError):
        start_hand(
            table(player(1), player(2)),
            hand_id=cast(Any, hand_id),
            dealer_seat=1,
            small_blind=5,
            big_blind=10,
            ordered_deck=DECK,
        )


def test_identifiers_are_opaque_and_not_trimmed() -> None:
    spaced_player_id = PlayerId(" player-1 ")
    spaced_hand_id = HandId(" hand-1 ")
    result = start_hand(
        table(SeatedPlayer(spaced_player_id, 1, 100), player(2)),
        hand_id=spaced_hand_id,
        dealer_seat=1,
        small_blind=5,
        big_blind=10,
        ordered_deck=DECK,
    )

    assert result.active_hand is not None
    assert result.active_hand.hand_id == spaced_hand_id
    assert result.active_hand.players[0].player_id == spaced_player_id


@pytest.mark.parametrize("dealer", [True, False, 1.0, 2.0, "1", None, 0, 9])
def test_dealer_seat_must_be_a_strict_integer(dealer: object) -> None:
    with pytest.raises(InvalidDealerError):
        start_hand(
            table(player(1), player(2)),
            hand_id=HandId("hand-1"),
            dealer_seat=cast(Any, dealer),
            small_blind=5,
            big_blind=10,
            ordered_deck=DECK,
        )


@pytest.mark.parametrize("dealer", [2, 4])
def test_dealer_seat_must_be_occupied_and_active(dealer: int) -> None:
    with pytest.raises(InvalidDealerError):
        begin(table(player(1), player(2, 0), player(3)), dealer=dealer)


def test_starting_while_a_hand_is_active_is_rejected() -> None:
    started = begin(table(player(1), player(2)), dealer=1)
    with pytest.raises(HandAlreadyActiveError):
        begin(started, dealer=1)


def test_inputs_are_unchanged_and_result_is_immutable() -> None:
    initial = table(player(1), player(4), player(8))
    initial_snapshot = initial
    deck = tuple(DECK)
    deck_snapshot = tuple(deck)

    result = begin(initial, dealer=4, deck=deck)

    assert initial == initial_snapshot
    assert initial.active_hand is None
    assert tuple(seated.stack for seated in initial.seats) == (100, 100, 100)
    assert deck == deck_snapshot
    with pytest.raises(FrozenInstanceError):
        cast(Any, result.seats[0]).stack = 0


def test_identical_inputs_produce_identical_outputs() -> None:
    initial = table(player(1), player(3), player(7))
    first = begin(initial, dealer=3)
    second = begin(initial, dealer=3)
    assert first == second


def test_private_cards_and_remaining_deck_are_absent_from_debug_representation() -> None:
    result = begin(table(player(1), player(2)), dealer=1)
    assert result.active_hand is not None
    debug_text = repr(result)
    assert "hole_cards" not in debug_text
    assert "remaining_deck" not in debug_text
    assert all(repr(card) not in debug_text for card in DECK)
