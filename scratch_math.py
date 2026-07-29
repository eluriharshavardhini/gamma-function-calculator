"""
scratch_math.py
================
Hand-built replacements for the math primitives needed by the Gamma function
implementation. No calls to Python's `math` module are used anywhere below.

Allowed per the assignment: arithmetic operators (+ - * / **), comparisons,
loops, and a hardcoded mathematical constant (PI). Everything else -- sqrt,
exp, sin -- is derived from first principles (Newton's method / Taylor series).
"""

# A mathematical constant is a fixed value, not a "built-in function" --
# we are still forbidden from calling math.pi, so this is typed out to
# 20 significant digits rather than imported.
PI = 3.14159265358979323846


def custom_abs(x):
    """
    Absolute value without calling abs()/math.fabs().

    Args:
        x (float): the input value.
    Returns:
        float: x if x is non-negative, otherwise -x.
    """
    return x if x >= 0 else -x


def custom_floor(x):
    """
    Floor without calling math.floor(). Works for the ranges we need.

    Args:
        x (float): the input value.
    Returns:
        int: the largest integer <= x.
    """
    n = int(x)  # int() truncates toward zero -- this is a language builtin,
    # not a math-library function, so it stays within the "from scratch" rule.
    if x < 0 and n != x:
        # int() truncated toward zero (e.g. int(-2.3) == -2), but floor(-2.3)
        # should be -3. Step down by one whenever truncation overshot.
        n -= 1
    return n


def custom_sqrt(x, tolerance=1e-15, max_iterations=100):
    """
    Square root via Newton's method (Newton-Raphson):
        guess_{n+1} = 0.5 * (guess_n + x / guess_n)

    Newton's method converges quadratically, but ONLY once the starting
    guess is reasonably close to the true root. For a very large or very
    small x (e.g. 1e150), starting the guess at x itself would take
    hundreds of iterations (each step barely more than halving the guess).

    To fix this: first reduce x into the bounded range [1, 4) by dividing
    or multiplying by 4 repeatedly (tracking how many times, as `k`), run
    Newton's method there (always converges in ~6-8 steps), then rescale
    the result by 2^k to undo the reduction. This mirrors how professional
    sqrt implementations use exponent extraction for a good first guess.

    Args:
        x (float): the value to take the square root of. Must be >= 0.
        tolerance (float): stop iterating once successive guesses differ
            by less than this amount.
        max_iterations (int): safety cap on the number of Newton steps.
    Returns:
        float: the square root of x.
    Raises:
        ValueError: if x is negative.
    """
    if x < 0:
        raise ValueError("custom_sqrt: cannot take the square root of a negative number.")
    if x == 0:
        return 0.0

    # --- Step 1: range reduction -----------------------------------------
    # Push x into [1, 4) by repeatedly dividing (or multiplying) by 4.
    # Each division by 4 corresponds to the true root being divided by 2,
    # which is why we rescale by 2**k at the very end.
    k = 0
    reduced_x = x
    while reduced_x >= 4:
        reduced_x /= 4
        k += 1
    while reduced_x < 1:
        reduced_x *= 4
        k -= 1
    # reduced_x is now in [1, 4), so its square root is in [1, 2) -- a safe,
    # bounded starting guess regardless of how large or small x was.

    # --- Step 2: Newton's method on the reduced value ---------------------
    guess = 1.5  # midpoint of the guaranteed [1, 2) result range
    for _ in range(max_iterations):
        next_guess = 0.5 * (guess + reduced_x / guess)
        if custom_abs(next_guess - guess) < tolerance:
            guess = next_guess
            break  # converged -- no need to keep iterating
        guess = next_guess

    # --- Step 3: undo the range reduction ---------------------------------
    return guess * (2 ** k)


def custom_exp(x, terms=200):
    """
    e^x via Taylor series around 0:
        e^x = sum_{n=0}^inf  x^n / n!
    Range reduction is used for large |x| so the series converges quickly
    and without overflow: e^x = (e^(x/2^k))^(2^k) for a suitable k.

    Args:
        x (float): the exponent.
        terms (int): maximum number of Taylor series terms to sum (a safety
            cap -- the loop usually breaks out early once terms get tiny).
    Returns:
        float: e raised to the power x.
    """
    # --- Step 1: range reduction -------------------------------------------
    # Pick k so that x/2^k is small (|value| < 0.01), then square back up.
    # A tighter reduction bound means fewer Taylor terms are needed and
    # less error accumulates through the repeated squaring at the end.
    k = 0
    reduced_x = x
    while custom_abs(reduced_x) > 0.01:
        reduced_x /= 2
        k += 1

    # --- Step 2: Taylor series on the reduced (small) value -----------------
    term = 1.0   # current term of the series (starts at the n=0 term, x^0/0! = 1)
    total = 1.0  # running sum of the series
    for n in range(1, terms):
        term *= reduced_x / n  # term_n = term_{n-1} * x / n  (builds x^n / n! incrementally)
        total += term
        if custom_abs(term) < 1e-18:
            break  # remaining terms are negligible -- stop early

    # --- Step 3: undo the range reduction by squaring k times ---------------
    # (e^(x/2^k))^(2^k) = e^x
    for _ in range(k):
        total *= total

    return total


def custom_ln(x, terms=60):
    """
    Natural log via argument reduction + Taylor series.

    Repeatedly take custom_sqrt() to push x close to 1 (this halves ln(x)
    each time: ln(x) = 2 * ln(sqrt(x))), then use the series
        ln(1+u) = u - u^2/2 + u^3/3 - u^4/4 + ...
    which converges quickly once |u| is small. Finally undo the reduction
    by multiplying back by 2^k.

    Args:
        x (float): the value to take the natural log of. Must be > 0.
        terms (int): maximum number of Taylor series terms to sum.
    Returns:
        float: the natural logarithm of x.
    Raises:
        ValueError: if x is not strictly positive.
    """
    if x <= 0:
        raise ValueError("custom_ln: x must be positive.")

    # --- Step 1: range reduction -------------------------------------------
    # Keep taking the square root until the value is close to 1
    # (within [0.667, 1.5]), where the ln(1+u) series converges fast.
    k = 0
    reduced_x = x
    while reduced_x > 1.5 or reduced_x < 0.667:
        reduced_x = custom_sqrt(reduced_x)
        k += 1

    # --- Step 2: Taylor series for ln(1 + u), where u is small --------------
    u = reduced_x - 1
    term = u       # current power of u (starts at u^1)
    total = 0.0
    for n in range(1, terms):
        # Alternating series: +u/1 - u^2/2 + u^3/3 - u^4/4 + ...
        total += term / n if n % 2 == 1 else -term / n
        term *= u  # advance to the next power of u
        if custom_abs(term) < 1e-20:
            break  # remaining terms are negligible -- stop early

    # --- Step 3: undo the range reduction -----------------------------------
    # ln(x) = 2^k * ln(reduced_x), since each sqrt() step halved the log.
    return total * (2 ** k)


def custom_sin(x, terms=30):
    """
    sin(x) via Taylor series around 0:
        sin(x) = sum_{n=0}^inf  (-1)^n * x^(2n+1) / (2n+1)!
    Range reduction brings x into [-PI, PI] first, since the raw Taylor
    series loses accuracy (and eventually diverges numerically) for large x.

    Args:
        x (float): the angle in radians.
        terms (int): maximum number of Taylor series terms to sum.
    Returns:
        float: sin(x).
    """
    # --- Step 1: range reduction ---------------------------------------
    # Bring x into (-PI, PI] by subtracting the nearest multiple of 2*PI.
    # custom_floor((x + PI) / two_pi) counts how many full 2*PI cycles to
    # remove so the remainder falls in the desired interval.
    two_pi = 2 * PI
    reduced_x = x - two_pi * custom_floor((x + PI) / two_pi)

    # --- Step 2: Taylor series on the reduced (small) value ---------------
    term = reduced_x        # first term: x^1 / 1!
    total = reduced_x
    x_squared = reduced_x * reduced_x
    for n in range(1, terms):
        # Each iteration advances two powers of x (x^(2n-1) -> x^(2n+1))
        # and folds in the alternating sign and the next two factorial terms.
        term *= -x_squared / ((2 * n) * (2 * n + 1))
        total += term
        if custom_abs(term) < 1e-18:
            break  # remaining terms are negligible -- stop early

    return total