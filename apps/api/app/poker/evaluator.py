"""Pure deterministic Texas Hold'em hand evaluation and showdown comparison."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import IntEnum
from itertools import combinations

from .errors import (
    DuplicateCardError,
    InvalidCardCollectionError,
    InvalidContenderError,
    InvalidContenderIdError,
    InvalidShowdownError,
)
from .model import Card, PlayerId, Rank, Suit


class HandCategory(IntEnum):
    """Hand strengths in explicit weakest-to-strongest order."""

    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9


@dataclass(frozen=True, slots=True, order=True)
class HandRank:
    """A complete, directly comparable poker hand rank."""

    category: HandCategory
    tie_break: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ShowdownContender:
    """A showdown-eligible player and their protected private cards."""

    player_id: PlayerId
    hole_cards: tuple[Card, Card] = field(repr=False)


@dataclass(frozen=True, slots=True)
class EvaluatedContender:
    """A contender's public showdown evaluation, without private cards."""

    player_id: PlayerId
    rank: HandRank


@dataclass(frozen=True, slots=True)
class ShowdownResult:
    """Deterministic showdown ranks and winners; no pot-settlement behavior."""

    contenders: tuple[EvaluatedContender, ...]
    strongest_rank: HandRank
    winner_ids: tuple[PlayerId, ...]


_RANK_VALUES: dict[Rank, int] = {
    Rank.TWO: 2,
    Rank.THREE: 3,
    Rank.FOUR: 4,
    Rank.FIVE: 5,
    Rank.SIX: 6,
    Rank.SEVEN: 7,
    Rank.EIGHT: 8,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 11,
    Rank.QUEEN: 12,
    Rank.KING: 13,
    Rank.ACE: 14,
}


def _materialize_cards(
    cards: Iterable[Card],
    *,
    minimum: int,
    maximum: int,
) -> tuple[Card, ...]:
    try:
        materialized = tuple(cards)
    except TypeError as error:
        raise InvalidCardCollectionError("cards must be an iterable") from error

    if not minimum <= len(materialized) <= maximum:
        if minimum == maximum:
            message = f"exactly {minimum} cards are required"
        else:
            message = f"between {minimum} and {maximum} cards are required"
        raise InvalidCardCollectionError(message)
    if any(
        type(card) is not Card
        or not isinstance(card.rank, Rank)
        or not isinstance(card.suit, Suit)
        for card in materialized
    ):
        raise InvalidCardCollectionError("every item must be a valid Card")
    if len(set(materialized)) != len(materialized):
        raise DuplicateCardError("cards must be unique")
    return materialized


def _straight_high(ranks: list[int]) -> int | None:
    unique = sorted(set(ranks), reverse=True)
    if unique == [14, 5, 4, 3, 2]:
        return 5
    if len(unique) == 5 and unique[0] - unique[-1] == 4:
        return unique[0]
    return None


def _evaluate_valid_five(cards: tuple[Card, ...]) -> HandRank:
    ranks = sorted((_RANK_VALUES[card.rank] for card in cards), reverse=True)
    counts: dict[int, int] = {}
    for rank in ranks:
        counts[rank] = counts.get(rank, 0) + 1
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    straight_high = _straight_high(ranks)
    flush = all(card.suit is cards[0].suit for card in cards[1:])

    if flush and straight_high is not None:
        return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_high,))
    if groups[0][0] == 4:
        return HandRank(HandCategory.FOUR_OF_A_KIND, (groups[0][1], groups[1][1]))
    if groups[0][0] == 3 and groups[1][0] == 2:
        return HandRank(HandCategory.FULL_HOUSE, (groups[0][1], groups[1][1]))
    if flush:
        return HandRank(HandCategory.FLUSH, tuple(ranks))
    if straight_high is not None:
        return HandRank(HandCategory.STRAIGHT, (straight_high,))
    if groups[0][0] == 3:
        kickers = sorted((rank for rank, count in counts.items() if count == 1), reverse=True)
        return HandRank(HandCategory.THREE_OF_A_KIND, (groups[0][1], *kickers))
    pairs = sorted((rank for rank, count in counts.items() if count == 2), reverse=True)
    if len(pairs) == 2:
        kicker = next(rank for rank, count in counts.items() if count == 1)
        return HandRank(HandCategory.TWO_PAIR, (pairs[0], pairs[1], kicker))
    if len(pairs) == 1:
        kickers = sorted((rank for rank, count in counts.items() if count == 1), reverse=True)
        return HandRank(HandCategory.ONE_PAIR, (pairs[0], *kickers))
    return HandRank(HandCategory.HIGH_CARD, tuple(ranks))


def evaluate_five(cards: Iterable[Card]) -> HandRank:
    """Evaluate exactly five unique, valid cards."""

    return _evaluate_valid_five(_materialize_cards(cards, minimum=5, maximum=5))


def evaluate_best(cards: Iterable[Card]) -> HandRank:
    """Return the strongest five-card rank available from five to seven cards."""

    materialized = _materialize_cards(cards, minimum=5, maximum=7)
    return max(_evaluate_valid_five(combo) for combo in combinations(materialized, 5))


def evaluate_showdown(
    community_cards: Iterable[Card],
    contenders: Iterable[ShowdownContender],
) -> ShowdownResult:
    """Evaluate two to eight contenders while validating all cards globally."""

    try:
        board = tuple(community_cards)
        entries = tuple(contenders)
    except TypeError as error:
        raise InvalidShowdownError("board and contenders must be iterable") from error

    if len(board) != 5:
        raise InvalidShowdownError("a showdown requires exactly five community cards")
    if not 2 <= len(entries) <= 8:
        raise InvalidShowdownError("a showdown requires between two and eight contenders")
    if any(type(entry) is not ShowdownContender for entry in entries):
        raise InvalidContenderError("every contender must be a ShowdownContender")

    for entry in entries:
        if type(entry.player_id) is not str or not entry.player_id.strip():
            raise InvalidContenderIdError("contender identifiers must be non-blank strings")
    player_ids: set[str] = set()
    for entry in entries:
        if entry.player_id in player_ids:
            raise InvalidContenderIdError("contender identifiers must be unique")
        player_ids.add(entry.player_id)

    if any(
        type(card) is not Card
        or not isinstance(card.rank, Rank)
        or not isinstance(card.suit, Suit)
        for card in board
    ):
        raise InvalidShowdownError("community cards must all be valid Card values")

    private_cards: list[Card] = []
    holes_by_contender: list[tuple[Card, ...]] = []
    for entry in entries:
        try:
            hole_cards = tuple(entry.hole_cards)
        except TypeError as error:
            raise InvalidContenderError("hole cards must be iterable") from error
        if len(hole_cards) != 2:
            raise InvalidContenderError("each contender requires exactly two hole cards")
        if any(
            type(card) is not Card
            or not isinstance(card.rank, Rank)
            or not isinstance(card.suit, Suit)
            for card in hole_cards
        ):
            raise InvalidContenderError("hole cards must all be valid Card values")
        holes_by_contender.append(hole_cards)
        private_cards.extend(hole_cards)

    all_cards = (*board, *private_cards)
    if len(set(all_cards)) != len(all_cards):
        raise DuplicateCardError("every card in a showdown must be globally unique")

    evaluated = tuple(
        EvaluatedContender(entry.player_id, evaluate_best((*board, *hole_cards)))
        for entry, hole_cards in zip(entries, holes_by_contender, strict=True)
    )
    strongest = max(entry.rank for entry in evaluated)
    winners = tuple(entry.player_id for entry in evaluated if entry.rank == strongest)
    return ShowdownResult(evaluated, strongest, winners)
