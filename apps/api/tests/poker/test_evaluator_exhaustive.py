import os
from collections import Counter
from itertools import combinations

import pytest

from app.poker import HandCategory, evaluate_five, standard_deck

EXPECTED_CATEGORY_TOTALS = {
    HandCategory.HIGH_CARD: 1_302_540,
    HandCategory.ONE_PAIR: 1_098_240,
    HandCategory.TWO_PAIR: 123_552,
    HandCategory.THREE_OF_A_KIND: 54_912,
    HandCategory.STRAIGHT: 10_200,
    HandCategory.FLUSH: 5_108,
    HandCategory.FULL_HOUSE: 3_744,
    HandCategory.FOUR_OF_A_KIND: 624,
    HandCategory.STRAIGHT_FLUSH: 40,
}


@pytest.mark.skipif(
    os.getenv("RUN_EXHAUSTIVE_POKER_TESTS") != "1",
    reason="set RUN_EXHAUSTIVE_POKER_TESTS=1 to classify every five-card hand",
)
def test_every_possible_five_card_hand_matches_mathematical_totals() -> None:
    observed = Counter(evaluate_five(hand).category for hand in combinations(standard_deck(), 5))

    assert sum(observed.values()) == 2_598_960
    assert observed == EXPECTED_CATEGORY_TOTALS
