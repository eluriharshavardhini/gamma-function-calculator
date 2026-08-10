import unittest
import math
import random

from gamma_scratch import gamma, GammaDomainError, GammaOverflowError
from scratch_math import custom_sqrt, custom_exp, custom_ln, custom_sin, PI


class TestGammaKnownValues(unittest.TestCase):
    """Check gamma(x) against known correct values, including the
    Gamma(n) = (n-1)! identity for positive integers."""

    def test_gamma_of_positive_integers(self):
        # Gamma(n) = (n-1)! -- e.g. Gamma(5) = 4! = 24
        self.assertAlmostEqual(gamma(1), 1, places=5)
        self.assertAlmostEqual(gamma(2), 1, places=5)
        self.assertAlmostEqual(gamma(3), 2, places=5)
        self.assertAlmostEqual(gamma(5), 24, places=5)
        self.assertAlmostEqual(gamma(6), 120, places=5)

    def test_gamma_of_half_integer(self):
        # Gamma(0.5) = sqrt(pi), a well-known closed-form special case
        self.assertAlmostEqual(gamma(0.5), math.sqrt(math.pi), places=5)

    def test_gamma_of_positive_decimal(self):
        # Gamma(4.5) has a known value, independently computable
        self.assertAlmostEqual(gamma(4.5), 11.631728, places=5)

    def test_gamma_of_negative_decimal(self):
        # Exercises Euler's reflection formula (x < 0.5 branch)
        self.assertAlmostEqual(gamma(-0.5), -3.544908, places=5)

    def test_gamma_matches_math_library_across_range(self):
        # Broad cross-check against Python's own math.gamma as the
        # reference implementation (this is AS-3 from our requirements).
        #
        # Relative error is used here instead of assertAlmostEqual's
        # decimal-places comparison, because that comparison checks
        # absolute difference -- meaningless for a value like Gamma(100),
        # which has over 150 digits. A relative error under 1e-8 confirms
        # the values agree to about 8 significant figures regardless of
        # magnitude.
        test_values = [0.1, 0.5, 1.5, 2.5, 3.7, 10.3, -1.5, -3.2, -10.7, 100]
        for x in test_values:
            with self.subTest(x=x):
                mine = gamma(x)
                reference = math.gamma(x)
                relative_error = abs(mine - reference) / abs(reference)
                self.assertLess(relative_error, 1e-8)


class TestGammaDomainErrors(unittest.TestCase):
    """Check that true poles (zero and negative integers) raise the
    correct, specific exception rather than crashing or returning
    a wrong number."""

    def test_zero_raises_domain_error(self):
        with self.assertRaises(GammaDomainError):
            gamma(0)

    def test_negative_integers_raise_domain_error(self):
        for x in [-1, -2, -3, -10, -50]:
            with self.subTest(x=x):
                with self.assertRaises(GammaDomainError):
                    gamma(x)

    def test_error_message_mentions_the_input(self):
        # Error messages must be "helpful to users" -- check the message
        # actually names the value that caused the problem.
        try:
            gamma(-2)
            self.fail("Expected GammaDomainError to be raised")
        except GammaDomainError as e:
            self.assertIn("-2", str(e))


class TestGammaOverflowAndUnderflow(unittest.TestCase):
    """Check the boundary behavior near the limits of 64-bit float range."""

    def test_within_range_does_not_raise(self):
        # x = 171 should still compute successfully
        try:
            result = gamma(171)
            self.assertTrue(result > 0)
        except GammaOverflowError:
            self.fail("gamma(171) should not raise GammaOverflowError")

    def test_beyond_boundary_raises_overflow_error(self):
        # x = 172 exceeds what a 64-bit float can represent
        with self.assertRaises(GammaOverflowError):
            gamma(172)

    def test_far_negative_underflows_to_zero_not_an_error(self):
        # Very negative non-integer x should return 0.0 gracefully,
        # not raise an exception (this is a documented boundary, AS-1).
        result = gamma(-200.5)
        self.assertEqual(result, 0.0)


class TestCustomMathPrimitives(unittest.TestCase):
    """Check the hand-built sqrt/exp/ln/sin functions independently,
    since gamma() depends entirely on their correctness."""

    def test_custom_sqrt_matches_math_sqrt(self):
        for x in [0, 1, 2, 4, 100, 0.25, 1e10, 1e-6]:
            with self.subTest(x=x):
                self.assertAlmostEqual(custom_sqrt(x), math.sqrt(x), places=6)

    def test_custom_sqrt_rejects_negative_input(self):
        with self.assertRaises(ValueError):
            custom_sqrt(-1)

    def test_custom_exp_matches_math_exp(self):
        for x in [0, 1, -1, 5, -5, 20, -20]:
            with self.subTest(x=x):
                tolerance = abs(math.exp(x)) * 1e-8
                self.assertAlmostEqual(
                    custom_exp(x), math.exp(x), delta=tolerance
                )

    def test_custom_ln_matches_math_log(self):
        for x in [0.5, 1, 2, 10, 100, 1000]:
            with self.subTest(x=x):
                self.assertAlmostEqual(custom_ln(x), math.log(x), places=6)

    def test_custom_ln_rejects_non_positive_input(self):
        with self.assertRaises(ValueError):
            custom_ln(0)
        with self.assertRaises(ValueError):
            custom_ln(-5)

    def test_custom_sin_matches_math_sin(self):
        for x in [0, PI / 2, PI, -PI / 2, 10, -7]:
            with self.subTest(x=x):
                self.assertAlmostEqual(custom_sin(x), math.sin(x), places=6)


class TestGammaRandomizedFuzz(unittest.TestCase):
    """
    Complements the hand-picked example tests above with randomized,
    dynamically-generated inputs -- this is sometimes called "fuzz" or
    "property-based" testing.

    Instead of checking a handful of numbers chosen by hand, this
    generates many pseudo-random inputs each run and checks they all
    satisfy the same rule: gamma(x) must agree with math.gamma(x) to
    within a tight relative error, across the whole supported domain.

    A fixed random seed is used so failures are reproducible -- if this
    ever fails, re-running it will generate the exact same inputs rather
    than a different random set each time, which makes debugging possible.
    """

    def test_random_positive_values_match_reference(self):
        random.seed(42)
        for _ in range(200):
            x = random.uniform(0.01, 170)
            # Skip values landing extremely close to a pole by chance;
            # not a meaningful test case since it's a measure-zero event
            # in true math but can happen with floating point rounding.
            if abs(x - round(x)) < 1e-9 and x < 1:
                continue
            with self.subTest(x=x):
                mine = gamma(x)
                reference = math.gamma(x)
                relative_error = abs(mine - reference) / abs(reference)
                self.assertLess(relative_error, 1e-6)

    def test_random_negative_non_integer_values_match_reference(self):
        random.seed(7)
        for _ in range(200):
            # Random negative non-integers, avoiding poles: pick a random
            # integer part and add a random fractional offset away from 0.
            integer_part = random.randint(-150, -1)
            fractional_part = random.uniform(0.05, 0.95)
            x = integer_part + fractional_part
            with self.subTest(x=x):
                mine = gamma(x)
                reference = math.gamma(x)
                relative_error = abs(mine - reference) / abs(reference)
                self.assertLess(relative_error, 1e-6)

    def test_random_values_never_crash_unexpectedly(self):
        # A broader sweep across the full supported range, confirming
        # every call either returns a float or raises one of our two
        # documented exceptions -- never an unhandled crash.
        random.seed(99)
        for _ in range(500):
            x = random.uniform(-165, 175)
            try:
                result = gamma(x)
                self.assertIsInstance(result, float)
            except (GammaDomainError, GammaOverflowError):
                pass  # expected, documented behavior -- not a failure


if __name__ == "__main__":
    unittest.main(verbosity=2)
