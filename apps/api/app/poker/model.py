"""Immutable, infrastructure-free values for the Hold'em domain foundation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import NewType

PlayerId = NewType("PlayerId", str)
HandId = NewType("HandId", str)

# Product documentation specifies eight players but not seat labels. Human-facing
# seats are therefore numbered 1 through 8; these values are domain seat numbers,
# never positions in a Python sequence.
MIN_SEAT = 1
MAX_SEAT = 8


class Suit(str, Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Rank(str, Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "jack"
    QUEEN = "queen"
    KING = "king"
    ACE = "ace"


@dataclass(frozen=True, slots=True)
class Card:
    rank: Rank
    suit: Suit


def standard_deck() -> tuple[Card, ...]:
    """Return the complete deck in stable enum declaration order."""

    return tuple(Card(rank, suit) for suit in Suit for rank in Rank)


@dataclass(frozen=True, slots=True)
class SeatedPlayer:
    player_id: PlayerId
    seat: int
    stack: int


@dataclass(frozen=True, slots=True)
class HandPlayer:
    player_id: PlayerId
    seat: int
    # Hole cards are explicitly private material and are omitted from repr/debug text.
    hole_cards: tuple[Card, Card] = field(repr=False)
    contribution: int = 0


class HandPhase(str, Enum):
    PREFLOP = "preflop"


@dataclass(frozen=True, slots=True)
class ActiveHand:
    hand_id: HandId
    phase: HandPhase
    players: tuple[HandPlayer, ...]
    dealer_seat: int
    small_blind_seat: int
    big_blind_seat: int
    first_to_act_seat: int
    pot: int
    # Deck continuation is protected recovery material, not public state/debug text.
    remaining_deck: tuple[Card, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class TableState:
    seats: tuple[SeatedPlayer, ...]
    active_hand: ActiveHand | None = None
