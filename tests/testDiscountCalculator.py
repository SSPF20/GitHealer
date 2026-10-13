import pytest
from discountCalculator import calculateFinalPrice

def testCalculateFinalPriceStandardDiscount():
    # If base price is 100 and discount is 20%, final price must be 80, not 20!
    expectedFinalPrice = 80.0
    actualPrice = calculateFinalPrice(100.0, 20.0)
    assert actualPrice == expectedFinalPrice

def testCalculateFinalPriceZeroDiscount():
    # If discount is 0%, price should remain 100
    expectedFinalPrice = 100.0
    actualPrice = calculateFinalPrice(100.0, 0.0)
    assert actualPrice == expectedFinalPrice