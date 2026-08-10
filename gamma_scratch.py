"""
gamma_scratch.py
================
Gamma function Gamma(x), implemented "from scratch" per the D2 constraint:
no built-in or library math functions are used anywhere in this file.
sqrt(), exp(), sin(), and the constant PI all come from scratch_math.py,
which derives them from first principles (Newton's method / Taylor series).

Public API:
    gamma(x) -> float
Raises:
    GammaDomainError    - x is zero or a negative integer (true poles)
    GammaOverflowError  - result exceeds standard 64-bit float range
"""

from scratch_math import (
    PI, custom_sqrt, custom_exp, custom_ln, custom_sin, custom_abs
)


class GammaDomainError(ValueError):
    """Raised when x falls on a true singularity of the Gamma function
    (zero or a negative integer)."""


class GammaOverflowError(OverflowError):
    """Raised when the true result would exceed standard 64-bit float range."""


# Lanczos coefficients (g=7, n=9) -- these are precomputed constants for the
# approximation itself, not calls to a math library. Using them is standard
# practice for the Lanczos method and does not violate the "from scratch"
# rule, since no built-in function computes them for us at runtime.
_G = 7
_LANCZOS_COEFFICIENTS = [
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7,
]


def _is_integer(x):
    """
    True if x represents a whole number (e.g. -3.0), without calling
    float.is_integer().

    Args:
        x (float): the value to check.
    Returns:
        bool: True if x has no fractional part.
    """
    return x == int(x)  # int(x) truncates; equal to x only when x is whole


def _lanczos_positive(x):
    """
    Lanczos approximation, valid for x > 0.5.
    Gamma(x) = sqrt(2*pi) * t^(z+0.5) * e^(-t) * A_g(z)
    where z = x - 1, t = z + g + 0.5, and A_g(z) is built from the
    Lanczos coefficients above.

    t^(z+0.5) alone overflows a 64-bit float well before x reaches the
    true domain limit (~171.6), even though the *final* Gamma value is
    still representable -- the tiny e^(-t) factor would have brought it
    back down. So instead of multiplying t^(z+0.5) and e^(-t) separately,
    we combine both into a single exponent and evaluate it once, using
    our own custom_ln():
        t^(z+0.5) * e^(-t) = e^{ (z+0.5)*ln(t) - t }

    Args:
        x (float): a value strictly greater than 0.5.
    Returns:
        float: Gamma(x).
    """
    z = x - 1

    # Build the Lanczos series A_g(z) = c0 + sum_i c_i / (z + i)
    a = _LANCZOS_COEFFICIENTS[0]
    for i in range(1, len(_LANCZOS_COEFFICIENTS)):
        a += _LANCZOS_COEFFICIENTS[i] / (z + i)

    t = z + _G + 0.5

    # Combine t^(z+0.5) and e^(-t) into one exponent (see docstring above)
    # to avoid the intermediate overflow that computing them separately
    # would cause for large x.
    combined_exponent = (z + 0.5) * custom_ln(t) - t
    power_and_exp_term = custom_exp(combined_exponent)

    return custom_sqrt(2 * PI) * power_and_exp_term * a


def gamma(x):
    """
    Compute Gamma(x) for any real x that is not a non-positive integer.

    Domain guards:
      - x == 0 or a negative integer -> GammaDomainError (true pole)
      - x < -160ish -> underflow to 0.0 (documented, not an error)
      - x > 171.5ish -> GammaOverflowError (exceeds float64 range)

    For x < 0.5 (and not a pole), Euler's reflection formula is used:
        Gamma(x) * Gamma(1 - x) = pi / sin(pi * x)
      => Gamma(x) = pi / (sin(pi * x) * Gamma(1 - x))

    Args:
        x (float): the point at which to evaluate the Gamma function.
    Returns:
        float: Gamma(x).
    Raises:
        GammaDomainError: if x is zero or a negative integer, or if x is
            numerically indistinguishable from a pole.
        GammaOverflowError: if the true result would exceed the range of
            a 64-bit float.
    """
    # --- Guard 1: true poles (zero and negative integers) ---
    if _is_integer(x) and x <= 0:
        raise GammaDomainError(
            f"Gamma(x) is undefined at x = {x}: zero and negative "
            "integers are poles."
        )

    # --- Guard 2: underflow region ---
    if x < -160:
        # Far enough negative that the true value underflows to 0.0 in
        # standard 64-bit floats; this is a graceful boundary, not an error.
        return 0.0

    # --- Guard 3: overflow region ---
    if x > 171.5:
        raise GammaOverflowError(
            f"Gamma({x}) exceeds the range representable by a 64-bit float."
        )

    # --- Case A: x < 0.5 -> use Euler's reflection formula ---
    # The Lanczos series below is only accurate for x > 0.5, so for smaller
    # (including negative, non-pole) x we "reflect" into that accurate range.
    if x < 0.5:
        denom = custom_sin(PI * x) * _lanczos_positive(1 - x)
        if custom_abs(denom) < 1e-300:
            # Extremely close to a pole but not exactly on one (e.g. due to
            # floating-point rounding); avoid a division blow-up and report
            # it as effectively undefined rather than returning a nonsense
            # huge number.
            raise GammaDomainError(
                f"Gamma({x}) is numerically unstable: too close to a pole."
            )
        return PI / denom

    # --- Case B: x >= 0.5 -> Lanczos approximation applies directly ---
    return _lanczos_positive(x)