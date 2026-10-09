from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from app.poker import (
    Card,
    DuplicateCardError,
    HandCategory,
    HandRank,
    InvalidCardCollectionError,
    InvalidContenderError,
    InvalidContenderIdError,
    InvalidShowdownError,
    PlayerId,
    Rank,
    ShowdownContender,
    Suit,
    evaluate_best,
    evaluate_five,
    evaluate_showdown,
)

RANKS = {
    "2": Rank.TWO,
    "3": Rank.THREE,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "T": Rank.TEN,
    "J": Rank.JACK,
    "Q": Rank.QUEEN,
    "K": Rank.KING,
    "A": Rank.ACE,
}
SUITS = {"c": Suit.CLUBS, "d": Suit.DIAMONDS, "h": Suit.HEARTS, "s": Suit.SPADES}


def cards(specification: str) -> tuple[Card, ...]:
    return tuple(Card(RANKS[token[0]], SUITS[token[1]]) for token in specification.split())


def rank(category: HandCategory, *tie_break: int) -> HandRank:
    return HandRank(category, tie_break)


@pytest.mark.parametrize(
    ("specification", "expected"),
    [
        ("As Jd 9h 6c 3s", rank(HandCategory.HIGH_CARD, 14, 11, 9, 6, 3)),
        ("As Ad Kh Tc 7s", rank(HandCategory.ONE_PAIR, 14, 13, 10, 7)),
        ("Ks Kd 8h 8c As", rank(HandCategory.TWO_PAIR, 13, 8, 14)),
        ("Qs Qd Qh 9c 2s", rank(HandCategory.THREE_OF_A_KIND, 12, 9, 2)),
        ("9s 8d 7h 6c 5s", rank(HandCategory.STRAIGHT, 9)),
        ("As Js 9s 6s 3s", rank(HandCategory.FLUSH, 14, 11, 9, 6, 3)),
        ("Qs Qd Qh 9c 9s", rank(HandCategory.FULL_HOUSE, 12, 9)),
        ("7s 7d 7h 7c As", rank(HandCategory.FOUR_OF_A_KIND, 7, 14)),
        ("9s 8s 7s 6s 5s", rank(HandCategory.STRAIGHT_FLUSH, 9)),
        ("As Ks Qs Js Ts", rank(HandCategory.STRAIGHT_FLUSH, 14)),
        ("As 2d 3h 4c 5s", rank(HandCategory.STRAIGHT, 5)),
    ],
)
def test_every_category_and_exact_tie_break(
    specification: str, expected: HandRank
) -> None:
    assert evaluate_five(cards(specification)) == expected


@pytest.mark.parametrize(
    ("weaker", "stronger"),
    [
        ("Ks Kd Ah Tc 7s", "As Ad 2h 3c 4s"),  # pair rank
        ("As Ad Qh Jc 9s", "Ac Ah Qd Js Ts"),  # pair kicker
        ("Qs Qd Jh Jc As", "Ks Kd 2h 2c 3s"),  # higher pair
        ("Ks Kd 7h 7c As", "Kh Kc 8h 8c 2s"),  # lower pair
        ("Ks Kd 8h 8c Qs", "Kh Kc 8d 8s As"),  # two-pair kicker
        ("Js Jd Jh Ac 2s", "Qs Qd Qh 3c 2d"),  # trip rank
        ("Qs Qd Qh 9c 7s", "Qc Qs Qh Tc 2d"),  # trip kicker
        ("8s 7d 6h 5c 4s", "9s 8d 7h 6c 5s"),  # straight high
        ("As 2d 3h 4c 5s", "6s 5d 4h 3c 2s"),  # wheel
        ("As Js 9s 6s 3s", "Ah Qh 8h 6h 3h"),  # flush kickers
        ("Js Jd Jh Ac As", "Qs Qd Qh 2c 2s"),  # full-house trips
        ("Qs Qd Qh 8c 8s", "Qc Qs Qh 9c 9s"),  # full-house pair
        ("6s 6d 6h 6c As", "7s 7d 7h 7c 2s"),  # quad rank
        ("7s 7d 7h 7c Ks", "7s 7d 7h 7c As"),  # quad kicker
        ("8s 7s 6s 5s 4s", "9h 8h 7h 6h 5h"),  # straight-flush high
    ],
)
def test_complete_tie_break_ordering(weaker: str, stronger: str) -> None:
    assert evaluate_five(cards(weaker)) < evaluate_five(cards(stronger))


def test_equal_rank_patterns_tie_without_suit_ordering() -> None:
    first = evaluate_five(cards("As Ad Kh Tc 7s"))
    second = evaluate_five(cards("Ac Ah Kd Ts 7h"))
    assert first == second


@pytest.mark.parametrize("specification", ["Qs Kd Ah 2c 3s", "Ks Ad 2h 3c 4s"])
def test_ace_does_not_wrap_around_in_a_straight(specification: str) -> None:
    assert evaluate_five(cards(specification)).category is HandCategory.HIGH_CARD


@pytest.mark.parametrize(
    ("specification", "expected"),
    [
        ("As Kd Qh Jc 9s 2d 3h", rank(HandCategory.HIGH_CARD, 14, 13, 12, 11, 9)),
        ("As Ad Kh Qc Js 2d 3h", rank(HandCategory.ONE_PAIR, 14, 13, 12, 11)),
        ("As Ad Kh Kc Qs Qd 2h", rank(HandCategory.TWO_PAIR, 14, 13, 12)),
        ("As Ad Ah Ks Kd Kh 2c", rank(HandCategory.FULL_HOUSE, 14, 13)),
        ("Qs Qd Qh 9s 9d 8s 8d", rank(HandCategory.FULL_HOUSE, 12, 9)),
        ("As Ad Ks Kd Qs Qd Jh", rank(HandCategory.TWO_PAIR, 14, 13, 12)),
        ("As Ks Qs 9s 7s 4s 2s", rank(HandCategory.FLUSH, 14, 13, 12, 9, 7)),
        ("As 2d 3h 4c 5s 6d 9h", rank(HandCategory.STRAIGHT, 6)),
        ("As Ks Qs Js Ts 9s 2d", rank(HandCategory.STRAIGHT_FLUSH, 14)),
        ("7s 7d 7h 7c As Kd 2h", rank(HandCategory.FOUR_OF_A_KIND, 7, 14)),
    ],
)
def test_best_five_handles_required_selection_cases(
    specification: str, expected: HandRank
) -> None:
    assert evaluate_best(cards(specification)) == expected


def test_best_hand_can_be_board_one_hole_or_both_hole_cards() -> None:
    board = cards("As Ks Qh Jc Ts")
    assert evaluate_best((*board, *cards("2d 3d"))) == rank(HandCategory.STRAIGHT, 14)
    assert evaluate_best((*cards("As Ad 7h 4c 2s"), *cards("Ac Kd"))) == rank(
        HandCategory.THREE_OF_A_KIND, 14, 13, 7
    )
    assert evaluate_best((*cards("As Kd 7h 4c 2s"), *cards("Ah Ac"))) == rank(
        HandCategory.THREE_OF_A_KIND, 14, 13, 7
    )


@pytest.mark.parametrize("specification", ["As Ks Qh Jc", "As Ks Qh Jc Ts 9d"])
def test_five_card_evaluation_requires_exactly_five(specification: str) -> None:
    with pytest.raises(InvalidCardCollectionError):
        evaluate_five(cards(specification))


@pytest.mark.parametrize(
    "specification", ["As Ks Qh Jc", "As Ks Qh Jc Ts 9d 8h 7c"]
)
def test_best_evaluation_requires_five_to_seven_cards(specification: str) -> None:
    with pytest.raises(InvalidCardCollectionError):
        evaluate_best(cards(specification))


def test_evaluation_rejects_duplicate_malformed_non_card_and_non_iterable_inputs() -> None:
    ace = cards("As")[0]
    with pytest.raises(DuplicateCardError):
        evaluate_five((ace, ace, *cards("Kd Qh Jc")))
    malformed = Card(cast(Any, "ace"), Suit.SPADES)
    with pytest.raises(InvalidCardCollectionError):
        evaluate_five((malformed, *cards("Kd Qh Jc Ts")))
    with pytest.raises(InvalidCardCollectionError):
        evaluate_five(cast(Any, ("As", *cards("Kd Qh Jc Ts"))))
    with pytest.raises(InvalidCardCollectionError):
        evaluate_five(cast(Any, None))


def contender(player_id: object, specification: str) -> ShowdownContender:
    return ShowdownContender(cast(Any, player_id), cast(Any, cards(specification)))


def test_showdown_has_clear_winner_and_kicker_winner() -> None:
    result = evaluate_showdown(
        cards("As Ad 7h 4c 2s"),
        (contender(PlayerId("king"), "Ks 3d"), contender(PlayerId("queen"), "Qs Jd")),
    )
    assert result.winner_ids == (PlayerId("king"),)
    assert result.strongest_rank == rank(HandCategory.ONE_PAIR, 14, 13, 7, 4)
    assert tuple(entry.player_id for entry in result.contenders) == ("king", "queen")


def test_board_plays_and_all_contenders_tie_in_input_order() -> None:
    players = (
        contender(PlayerId("third"), "2c 3d"),
        contender(PlayerId("first"), "4c 5d"),
        contender(PlayerId("second"), "6c 7d"),
    )
    result = evaluate_showdown(cards("As Ks Qh Jc Ts"), players)
    assert result.winner_ids == ("third", "first", "second")


def test_two_way_tie_excludes_weaker_player_and_preserves_winner_order() -> None:
    result = evaluate_showdown(
        cards("As Kd Qh 7c 2s"),
        (
            contender(PlayerId("zeta"), "Jc Ts"),
            contender(PlayerId("weaker"), "Ac 3d"),
            contender(PlayerId("alpha"), "Jh Tc"),
        ),
    )
    assert result.winner_ids == ("zeta", "alpha")


def test_showdown_is_deterministic_immutable_and_does_not_mutate_inputs() -> None:
    board = cards("As Kd Qh 7c 2s")
    players = (contender(PlayerId("a"), "Jc Ts"), contender(PlayerId("b"), "Ac 3d"))
    snapshot = (board, players)
    first = evaluate_showdown(board, players)
    second = evaluate_showdown(board, players)
    assert first == second
    assert (board, players) == snapshot
    with pytest.raises(FrozenInstanceError):
        cast(Any, first).winner_ids = ()


def test_showdown_result_repr_does_not_expose_private_cards() -> None:
    private = cards("Jc Ts Ac 3d")
    result = evaluate_showdown(
        cards("As Kd Qh 7c 2s"),
        (contender(PlayerId("a"), "Jc Ts"), contender(PlayerId("b"), "Ac 3d")),
    )
    debug_text = repr(result)
    assert "hole_cards" not in debug_text
    assert all(repr(card) not in debug_text for card in private)


@pytest.mark.parametrize("count", [1, 9])
def test_showdown_rejects_invalid_contender_count(count: int) -> None:
    players = tuple(contender(PlayerId(f"p{index}"), "2c 3d") for index in range(count))
    with pytest.raises(InvalidShowdownError):
        evaluate_showdown(cards("As Ks Qh Jc Ts"), players)


def test_showdown_rejects_invalid_board_and_hole_card_counts() -> None:
    players = (contender(PlayerId("a"), "2c 3d"), contender(PlayerId("b"), "4c 5d"))
    with pytest.raises(InvalidShowdownError):
        evaluate_showdown(cards("As Ks Qh Jc"), players)
    malformed = ShowdownContender(PlayerId("a"), cast(Any, cards("2c")))
    with pytest.raises(InvalidContenderError):
        evaluate_showdown(cards("As Ks Qh Jc Ts"), (malformed, players[1]))


@pytest.mark.parametrize("player_id", [None, 1, True, "", "   ", [], {}])
def test_showdown_rejects_invalid_contender_identifiers(player_id: object) -> None:
    with pytest.raises(InvalidContenderIdError):
        evaluate_showdown(
            cards("As Ks Qh Jc Ts"),
            (contender(player_id, "2c 3d"), contender(PlayerId("valid"), "4c 5d")),
        )


def test_showdown_rejects_duplicate_contender_identifier() -> None:
    with pytest.raises(InvalidContenderIdError):
        evaluate_showdown(
            cards("As Ks Qh Jc Ts"),
            (contender(PlayerId("same"), "2c 3d"), contender(PlayerId("same"), "4c 5d")),
        )


@pytest.mark.parametrize(
    ("board", "first", "second"),
    [
        ("As As Qh Jc Ts", "2c 3d", "4c 5d"),  # board
        ("As Ks Qh Jc Ts", "2c 2c", "4c 5d"),  # one player's holes
        ("As Ks Qh Jc Ts", "As 2c", "4c 5d"),  # board and player
        ("As Ks Qh Jc Ts", "2c 3d", "2c 5d"),  # different players
    ],
)
def test_showdown_rejects_every_global_duplicate_location(
    board: str, first: str, second: str
) -> None:
    with pytest.raises(DuplicateCardError):
        evaluate_showdown(
            cards(board),
            (contender(PlayerId("a"), first), contender(PlayerId("b"), second)),
        )


def test_showdown_rejects_malformed_cards_non_contenders_and_non_iterables() -> None:
    malformed = Card(Rank.ACE, cast(Any, "spades"))
    players = (contender(PlayerId("a"), "2c 3d"), contender(PlayerId("b"), "4c 5d"))
    with pytest.raises(InvalidShowdownError):
        evaluate_showdown((malformed, *cards("Ks Qh Jc Ts")), players)
    with pytest.raises(InvalidContenderError):
        evaluate_showdown(cards("As Ks Qh Jc Ts"), cast(Any, (players[0], "player")))
    with pytest.raises(InvalidShowdownError):
        evaluate_showdown(cast(Any, None), players)
    with pytest.raises(InvalidShowdownError):
        evaluate_showdown(cards("As Ks Qh Jc Ts"), cast(Any, None))
