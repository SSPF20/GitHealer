def calculateFinalPrice(basePrice: float, discountPercentage: float) -> float:
    if discountPercentage < 0:
        raise ValueError("Discount percentage cannot be negative")
    
    return basePrice * (1.0 - discountPercentage / 100.0)
