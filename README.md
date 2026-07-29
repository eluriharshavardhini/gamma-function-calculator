# Gamma Function Calculator — Γ(x)

A scientific calculator that computes the Gamma function, Γ(x), implemented **entirely from scratch** in Python — no calls to the `math` module anywhere in the calculation logic. Built for SOEN 6011 (Software Engineering Processes), Deliverable 2.

## What is the Gamma Function?

The Gamma function extends the factorial to real (and complex) numbers. For positive integers:

```
Γ(n) = (n − 1)!
```

For example, Γ(5) = 4! = 24, and Γ(6) = 5! = 120. Unlike the factorial, Γ(x) is also defined for non-integers and negative non-integers (e.g. Γ(4.5) ≈ 11.632).

## Why "From Scratch"?

This project's constraint is that no built-in or library math functions (`math.sqrt`, `math.exp`, `math.sin`, `math.pi`, etc.) may be used. Instead, every primitive the Gamma function needs is derived from first principles:

| Function | Method |
|---|---|
| `custom_sqrt` | Newton's method (Newton-Raphson), with range reduction into `[1, 4)` for fast, reliable convergence at any magnitude |
| `custom_exp` | Taylor series expansion, with range reduction to avoid overflow for large inputs |
| `custom_ln` | Taylor series on `ln(1+u)`, with repeated square-root reduction to bring the argument close to 1 |
| `custom_sin` | Taylor series expansion, with range reduction into `(-π, π]` |
| `PI` | Hardcoded mathematical constant (not computed via `math.pi`) |

These primitives are combined using the **Lanczos approximation** (with Euler's reflection formula for negative arguments) to compute Γ(x) across its full valid domain.

## Features

- Full support for positive, negative, and fractional real inputs
- Domain error handling for true poles (zero and negative integers)
- Overflow/underflow handling near the limits of 64-bit float precision
- A calculator-style Tkinter GUI — enter digits on a keypad and press **Γ(x)** to evaluate, just like a physical calculator
- Accuracy validated against Python's built-in `math.gamma` to within ~1e-11 relative error across the supported domain

## Project Structure

```
gamma-function-calculator/
├── scratch_math.py    # Custom sqrt, exp, ln, sin, and the PI constant
├── gamma_scratch.py   # Gamma(x), built on scratch_math.py
├── gamma_gui.py        # Tkinter calculator GUI (entry point)
├── README.md
└── LICENSE
```

## Requirements

- Python 3.8 or later
- Tkinter (bundled with standard Python installations on Windows/macOS; on Linux, install with `sudo apt install python3-tk` if missing)

No third-party packages are required.

## How to Run

```bash
git clone https://github.com/eluriharshavardhini/gamma-function-calculator.git
cd gamma-function-calculator
python3 gamma_gui.py
```

## Usage

1. Type a value for x using the keypad (or your keyboard — digits, `.`, `±` via the sign key, `⌫` to backspace).
2. Press **Γ(x)** to evaluate.
3. The result appears on the display, formatted to 6 decimal places.

**Example:**

| Input | Output |
|---|---|
| `5` | Γ(5) = 24.000000 |
| `4.5` | Γ(4.5) = 11.631728 |
| `-0.5` | Γ(-0.5) = -3.544908 |
| `0` | Undefined here (zero is a pole) |
| `-2` | Undefined here (negative integers are poles) |

## Valid Domain

Γ(x) is defined for all real x **except** zero and negative integers. This implementation additionally supports:
- Approximately `-160 < x ≤ 171.5` — outside this range, results either underflow to `0.0` or exceed the range representable by a 64-bit float, and are reported accordingly rather than silently producing incorrect output.

## Author

Harshavardhini Eluri — Concordia University, SOEN 6011, Summer 2026

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
