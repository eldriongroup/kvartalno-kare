"""Public API for the pure poker-domain foundation."""

from .errors import (
    HandAlreadyActiveError,
    InsufficientPlayersError,
    InvalidBlindsError,
    InvalidDealerError,
    InvalidDeckError,
    InvalidHandIdError,
    InvalidSeatingError,
    PokerDomainError,
)
from .model import (
    MAX_SEAT,
    MIN_SEAT,
    ActiveHand,
    Card,
    HandId,
    HandPhase,
    HandPlayer,
    PlayerId,
    Rank,
    SeatedPlayer,
    Suit,
    TableState,
    standard_deck,
)
from .transition import start_hand

__all__ = [
    "MAX_SEAT",
    "MIN_SEAT",
    "ActiveHand",
    "Card",
    "HandAlreadyActiveError",
    "HandId",
    "HandPhase",
    "HandPlayer",
    "InsufficientPlayersError",
    "InvalidBlindsError",
    "InvalidDealerError",
    "InvalidDeckError",
    "InvalidHandIdError",
    "InvalidSeatingError",
    "PlayerId",
    "PokerDomainError",
    "Rank",
    "SeatedPlayer",
    "Suit",
    "TableState",
    "standard_deck",
    "start_hand",
]
