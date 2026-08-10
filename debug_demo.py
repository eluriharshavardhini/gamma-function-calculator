"""
debug_demo.py
=============
A small driver script used to demonstrate the pdb debugger against
gamma_scratch.py, for D3 Problem 7 (debugger snapshot requirement).

Run with:
    python -m pdb debug_demo.py

This is a one-time demonstration tool, not part of the actual project.
"""

from gamma_scratch import gamma

result = gamma(4.5)
print(f"Gamma(4.5) = {result}")