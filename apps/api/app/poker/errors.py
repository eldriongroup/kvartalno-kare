"""Transport-agnostic errors raised by the poker domain."""


class PokerDomainError(ValueError):
    """Base class for an invalid poker-domain transition or state."""


class HandAlreadyActiveError(PokerDomainError):
    """Raised when a hand is started while the table already has one."""


class InsufficientPlayersError(PokerDomainError):
    """Raised when fewer than two players have chips at the table."""


class InvalidDealerError(PokerDomainError):
    """Raised when the supplied dealer seat is invalid or inactive."""


class InvalidHandIdError(PokerDomainError):
    """Raised when the supplied hand identifier is invalid."""


class InvalidBlindsError(PokerDomainError):
    """Raised when the blind structure is not valid."""


class InvalidDeckError(PokerDomainError):
    """Raised when the supplied deck is not one complete standard deck."""


class InvalidSeatingError(PokerDomainError):
    """Raised for invalid seats, identities, or table stacks."""


class InvalidCardCollectionError(PokerDomainError):
    """Raised when cards supplied for hand evaluation are structurally invalid."""


class DuplicateCardError(PokerDomainError):
    """Raised when the same card occurs more than once in an evaluation."""


class InvalidShowdownError(PokerDomainError):
    """Raised when a showdown has an invalid board or contender collection."""


class InvalidContenderError(PokerDomainError):
    """Raised when a showdown contender or their private cards are invalid."""


class InvalidContenderIdError(PokerDomainError):
    """Raised when a showdown contender identifier is invalid or duplicated."""
