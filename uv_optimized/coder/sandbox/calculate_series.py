def calculate_pi_like_series(terms: int = 1_000_000) -> float:
    total = 0.0
    sign = 1.0
    for i in range(terms):
        denominator = 2 * i + 1
        total += sign / denominator
        sign = -sign
    return total * 4


if __name__ == "__main__":
    result = calculate_pi_like_series()
    print(result)
