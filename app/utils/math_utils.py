# app/utils/math_utils.py
"""
Pure Python implementations of financial calculations.
Replaces numpy-financial to reduce bundle size by ~100MB.
"""

def calculate_npv(discount_rate, cash_flows):
    """
    Calculate Net Present Value (NPV) using pure Python.

    Formula: NPV = Σ [CF_t / (1 + r)^t] for t = 0 to n

    Args:
        discount_rate (float): Discount rate per period (e.g., 0.01 for 1% monthly)
        cash_flows (list): List of cash flows for each period (index 0 is period 0)

    Returns:
        float: Net Present Value, or None if calculation fails

    Example:
        >>> calculate_npv(0.01, [-1000, 100, 100, 100, 1100])
        # Returns NPV for initial investment of -1000 and 4 periods of cash flows
    """
    if not cash_flows:
        return None

    try:
        npv = 0.0
        for period, cash_flow in enumerate(cash_flows):
            # NPV formula: CF / (1 + r)^t
            npv += cash_flow / ((1 + discount_rate) ** period)
        return npv
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None


def calculate_irr(cash_flows, max_iterations=100, tolerance=1e-6):
    """
    Calculate Internal Rate of Return (IRR) using Newton-Raphson method.

    IRR is the discount rate where NPV = 0.
    Uses iterative approximation starting from an initial guess.

    Args:
        cash_flows (list): List of cash flows for each period
        max_iterations (int): Maximum iterations before giving up (default: 100)
        tolerance (float): Acceptable error margin for NPV ≈ 0 (default: 1e-6)

    Returns:
        float: IRR as a decimal (e.g., 0.15 = 15%), or None if no convergence

    Algorithm:
        1. Start with initial guess (10% = 0.10)
        2. Calculate NPV at current rate
        3. Calculate derivative (NPV slope)
        4. Adjust rate using Newton-Raphson: rate_new = rate_old - NPV / derivative
        5. Repeat until NPV ≈ 0 or max iterations reached

    Edge Cases:
        - Returns None if cash flows are empty
        - Returns None if all cash flows have same sign (no IRR exists)
        - Returns None if derivative is zero (can't improve guess)
        - Returns None if no convergence after max_iterations
    """
    if not cash_flows or len(cash_flows) < 2:
        return None

    # CRITICAL: Check if all cash flows have the same sign (no IRR exists)
    # This MUST happen BEFORE entering the iteration loop for performance
    # Example edge case: Excel with all positive cash flows (no investment) = immediate None
    has_positive = any(cf > 0 for cf in cash_flows)
    has_negative = any(cf < 0 for cf in cash_flows)
    if not (has_positive and has_negative):
        return None  # IRR requires sign changes in cash flows (investment + returns)

    try:
        # Initial guess: 10% (0.10)
        rate = 0.10

        for iteration in range(max_iterations):
            # Calculate NPV at current rate
            npv = sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cash_flows))

            # Check if we're close enough to zero
            if abs(npv) < tolerance:
                return rate

            # Calculate derivative (dNPV/dr) for Newton-Raphson
            # Derivative formula: dNPV/dr = Σ [-t * CF_t / (1 + r)^(t+1)]
            derivative = sum(-t * cf / ((1 + rate) ** (t + 1)) for t, cf in enumerate(cash_flows))

            # Avoid division by zero
            if abs(derivative) < 1e-10:
                return None  # Can't improve guess

            # Newton-Raphson step: x_new = x_old - f(x) / f'(x)
            rate = rate - npv / derivative

            # Sanity check: rate shouldn't be too extreme
            if rate < -0.99 or rate > 10:  # IRR between -99% and 1000%
                return None  # Unrealistic rate, likely no convergence

        # Max iterations reached without convergence
        return None

    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None
