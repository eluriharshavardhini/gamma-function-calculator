"""
gamma_gui.py
============
A calculator-style Tkinter GUI for the Gamma function -- styled to read as
a professional scientific instrument (muted graphite body, monospace LCD
screen) rather than a bright/toy interface.

Run with:
    python3 gamma_gui.py

Files:
    scratch_math.py  - custom sqrt/exp/ln/sin/PI (no math module calls)
    gamma_scratch.py - Gamma(x) built entirely from scratch_math.py
    gamma_gui.py     - this file: GUI + exception handling + user-facing errors
"""

import tkinter as tk
from collections import namedtuple

from gamma_scratch import gamma, GammaDomainError, GammaOverflowError

# --- Color palette (muted / professional, not neon) -----------------------
# Kept as named constants (rather than inline hex strings scattered through
# the widget code) so the whole theme can be re-tuned from one place.
BODY_BG = "#2a2d33"           # calculator casing: graphite, not pure black
SCREEN_BG = "#14161a"         # LCD screen background
SCREEN_FG = "#dfe4e8"         # main readout text: soft off-white, not neon
SCREEN_SUBFG = "#7d8590"      # small history line above the readout
SCREEN_ERR = "#e0a4a4"        # muted rose for errors, not bright red

DISPLAY_FONT_FAMILY = "Consolas"   # monospace, genuine calculator feel
LABEL_FONT_FAMILY = "Segoe UI"     # used for button labels (not the screen)

# KeyStyle bundles a key's resting/active colors into one object, instead
# of passing three separate bg/fg/active_bg arguments to _make_key() for
# every button. This both reduces argument count (Pylint's
# too-many-arguments check) and groups genuinely related values together,
# which is the actual point of the refactor rather than just quieting a
# warning.
# KeyStyle is a namedtuple -- a plain data container by design, so it
# intentionally has zero methods. Pylint's "too few public methods" check
# is meant to catch classes that should have been simple data structures;
# this already is one, so the warning doesn't apply here.
KeyStyle = namedtuple(  # pylint: disable=too-few-public-methods
    "KeyStyle", ["bg", "fg", "active_bg"]
)

KEY_NUM_STYLE = KeyStyle(
    bg="#3a3d44", fg="#e8eaed", active_bg="#484c54"
)  # digit keys (0-9)

KEY_FUNC_STYLE = KeyStyle(
    bg="#33363c", fg="#c7ccd1", active_bg="#41454c"
)  # C, backspace, +/-, decimal point

KEY_ACCENT_STYLE = KeyStyle(
    bg="#4d6e8c", fg="#f2f5f7", active_bg="#3e5a74"
)  # muted steel blue for the Gamma ("=") key


# GammaApp inherits tk.Tk's public interface (mainloop, etc.) and adds
# __init__. Every calculator-specific method is deliberately prefixed
# with `_` (encapsulation: none of them are meant to be called from
# outside this class, only bound internally to button commands and
# keyboard events), so Pylint sees zero "public" methods even though
# the class is fully functional. This is intentional design, not an
# oversight.
class GammaApp(tk.Tk):  # pylint: disable=too-few-public-methods
    """
    The main application window.

    Behaves like a physical/phone calculator: digits are typed one at a
    time onto a running "current_entry" string, and pressing the Gamma
    key evaluates that entry and shows the result in its place -- exactly
    like pressing "=" replaces the input with a result.
    """

    def __init__(self):
        super().__init__()
        self.title("Gamma Function Calculator")
        self.configure(bg=BODY_BG)

        # --- Calculator state ------------------------------------------------
        # current_entry: the string currently shown on the main display line.
        #     While typing, this is the raw number being built (e.g. "-4.5").
        #     After pressing Gamma(x), it becomes the formatted result or an
        #     error message instead.
        # just_evaluated: True immediately after Gamma(x) was pressed. The
        #     next digit typed should start a brand-new entry rather than
        #     appending to the old result (same behavior as a real calculator).
        # has_error: True when the display is currently showing an error
        #     message rather than a number; used to pick the display color
        #     and to know that the next keypress should also start fresh.
        self.current_entry = "0"
        self.just_evaluated = False
        self.has_error = False

        self._build_screen()
        self._build_keypad()

        self._refresh_screen()

        # Let the window size itself to its contents (rather than a hardcoded
        # geometry, which previously cropped the bottom row of keys), then
        # lock that size so the layout can't be resized into something that
        # breaks the grid.
        self.update_idletasks()
        self.geometry("")
        self.resizable(False, False)

    # ----------------------------------------------------------------
    # Layout
    # ----------------------------------------------------------------
    def _build_screen(self):
        """Build the LCD-style display: a small history line on top
        (e.g. "Gamma(5) =") and a large readout line below it (the value
        currently being typed, or the result/error after evaluating)."""
        outer = tk.Frame(self, bg=BODY_BG)
        outer.pack(fill="x", padx=16, pady=(16, 10))

        # A 1px border frames the screen, visually separating it from the
        # graphite body -- mimicking the recessed LCD panel of a real
        # calculator rather than a flat colored rectangle.
        screen_frame = tk.Frame(
            outer, bg=SCREEN_BG, highlightbackground="#000000",
            highlightthickness=1
        )
        screen_frame.pack(fill="x")

        self.history_var = tk.StringVar(value="")
        tk.Label(
            screen_frame,
            textvariable=self.history_var,
            font=(DISPLAY_FONT_FAMILY, 11),
            bg=SCREEN_BG,
            fg=SCREEN_SUBFG,
            anchor="e",  # right-aligned, like a real calculator's history line
        ).pack(fill="x", padx=14, pady=(12, 0))

        self.display_var = tk.StringVar(value="0")
        self.display_label = tk.Label(
            screen_frame,
            textvariable=self.display_var,
            font=(DISPLAY_FONT_FAMILY, 30, "bold"),
            bg=SCREEN_BG,
            fg=SCREEN_FG,
            anchor="e",
            justify="right",
        )
        self.display_label.pack(fill="x", padx=14, pady=(2, 14))

    def _build_keypad(self):
        """Build the number pad + function keys + the Gamma evaluate key,
        laid out in a grid exactly like a physical calculator."""
        keypad = tk.Frame(self, bg=BODY_BG)
        keypad.pack(padx=16, pady=(0, 16))

        # Row 0: function keys (clear, backspace, sign toggle, decimal point)
        self._make_key(keypad, "C", self._on_clear, KEY_FUNC_STYLE, (0, 0))
        self._make_key(
            keypad, "\u232b", self._on_backspace, KEY_FUNC_STYLE, (0, 1)
        )
        self._make_key(
            keypad, "\u00b1", self._on_sign, KEY_FUNC_STYLE, (0, 2)
        )
        self._make_key(
            keypad, ".", lambda: self._on_digit("."), KEY_FUNC_STYLE, (0, 3)
        )

        # Rows 1-3: digits 7-9, 4-6, 1-3 (standard calculator digit layout)
        digit_rows = [("7", "8", "9"), ("4", "5", "6"), ("1", "2", "3")]
        for r, row_digits in enumerate(digit_rows, start=1):
            for c, digit in enumerate(row_digits):
                # default-argument trick (d=digit) captures the current loop
                # value; without it every button would end up bound to the
                # last digit in the loop due to Python's late-binding closures.
                self._make_key(
                    keypad, digit, lambda d=digit: self._on_digit(d),
                    KEY_NUM_STYLE, (r, c)
                )

        # Row 4: "0" spans two columns (matches the classic calculator layout
        # where 0 is wider than the other digit keys)
        self._make_key(
            keypad, "0", lambda: self._on_digit("0"),
            KEY_NUM_STYLE, (4, 0), columnspan=2
        )

        # Gamma key: spans rows 1-4 on the right-hand column, visually playing
        # the role a normal calculator's tall "=" key plays.
        gamma_btn = tk.Button(
            keypad,
            text="\u0393(x)",
            font=(LABEL_FONT_FAMILY, 15, "bold"),
            bg=KEY_ACCENT_STYLE.bg,
            fg=KEY_ACCENT_STYLE.fg,
            activebackground=KEY_ACCENT_STYLE.active_bg,
            activeforeground=KEY_ACCENT_STYLE.fg,
            bd=0,
            relief="flat",
            width=6,
            cursor="hand2",
            command=self._on_evaluate,
        )
        gamma_btn.grid(
            row=1, column=3, rowspan=4, padx=5, pady=5, sticky="nsew"
        )

        # Keyboard shortcuts, so a live demo doesn't require clicking every
        # digit with the mouse -- typing on the physical keyboard works too.
        self.bind("<Return>", lambda event: self._on_evaluate())
        self.bind("<BackSpace>", lambda event: self._on_backspace())
        for d in "0123456789":
            self.bind(d, lambda event, d=d: self._on_digit(d))
        self.bind(".", lambda event: self._on_digit("."))
        self.bind("<Escape>", lambda event: self._on_clear())

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # 6 parameters (one over the default limit of 5) after already
    # bundling color triplets into `style` and grid coordinates into
    # `position`. Merging further -- e.g. folding `columnspan` into
    # `position` or combining `label`/`command` into one object -- would
    # obscure what each call site is actually doing rather than clarify
    # it, since this is a small internal widget-builder helper, not a
    # public API. Kept explicit and documented here rather than silently
    # suppressed.
    def _make_key(self, parent, label, command, style, position,
                  columnspan=1):
        """
        Create one flat, borderless calculator key and place it in the grid.

        Args:
            parent: the container frame the button is placed in.
            label (str): the text shown on the key.
            command: the function to call when the key is pressed.
            style (KeyStyle): resting/active colors for this key.
            position (tuple[int, int]): (row, col) grid position.
            columnspan (int): how many grid columns the key should occupy
                (used for the wide "0" key).
        Returns:
            tk.Button: the created button (rarely needed by the caller, but
                returned for consistency / potential future styling tweaks).
        """
        row, col = position
        btn = tk.Button(
            parent,
            text=label,
            font=(LABEL_FONT_FAMILY, 14, "bold"),
            bg=style.bg,
            fg=style.fg,
            activebackground=style.active_bg,
            activeforeground=style.fg,
            bd=0,
            relief="flat",
            # wide keys (like "0") need double the width
            width=5 if columnspan == 1 else 11,
            height=2,
            cursor="hand2",
            command=command,
        )
        btn.grid(
            row=row, column=col, columnspan=columnspan,
            padx=5, pady=5, sticky="nsew"
        )
        return btn

    # ----------------------------------------------------------------
    # Keypad behaviour
    # ----------------------------------------------------------------
    def _on_digit(self, digit):
        """Handle a digit (or decimal point) key press."""
        if self.has_error or self.just_evaluated:
            # A fresh number should replace whatever was on screen -- either
            # a finished result or an error message -- exactly like typing
            # after "=" on a normal calculator.
            self._start_fresh_entry()

        if digit == ".":
            # Only one decimal point is allowed per number.
            if "." not in self.current_entry:
                self.current_entry += "."
        else:
            if self.current_entry == "0":
                # Replace the placeholder "0" instead of appending to it
                # (otherwise typing "5" would show "05").
                self.current_entry = digit
            else:
                self.current_entry += digit

        self._refresh_screen()

    def _on_sign(self):
        """Handle the +/- key: toggle the sign of the number being typed."""
        if self.has_error or self.just_evaluated:
            self._start_fresh_entry()

        if self.current_entry.startswith("-"):
            # remove existing minus sign
            self.current_entry = self.current_entry[1:]
        elif self.current_entry != "0":
            # add a minus sign
            self.current_entry = "-" + self.current_entry
        self._refresh_screen()

    def _on_backspace(self):
        """Handle the backspace key: delete the last typed character."""
        if self.has_error or self.just_evaluated:
            # After a result/error, backspace behaves like clear rather than
            # editing the result character-by-character.
            self._on_clear()
            return
        self.current_entry = self.current_entry[:-1]
        if self.current_entry in ("", "-"):
            # Don't allow the display to go fully blank or show a bare "-".
            self.current_entry = "0"
        self._refresh_screen()

    def _on_clear(self):
        """Handle the C key: reset the calculator to its initial state."""
        self.current_entry = "0"
        self.history_var.set("")
        self.has_error = False
        self.just_evaluated = False
        self._refresh_screen()

    def _start_fresh_entry(self):
        """Reset internal state so the next digit starts a brand-new number,
        without touching the screen directly (the caller updates it next)."""
        self.current_entry = "0"
        self.history_var.set("")
        self.has_error = False
        self.just_evaluated = False

    def _on_evaluate(self):
        """Handle the Gamma(x) key: parse the current entry as a number,
        compute Gamma(x), and show either the result or a helpful error."""
        try:
            x = float(self.current_entry)
        except ValueError:
            # This shouldn't normally happen since only digits/./- can be
            # typed, but it's kept as a safety net for unexpected states.
            self._show_error(self.current_entry, "Invalid entry")
            return

        try:
            result = gamma(x)
            self.history_var.set(f"\u0393({_format_x(x)}) =")
            self.current_entry = f"{result:.6f}"  # 6 decimal places (NFR-2.2)
            self.just_evaluated = True
            self.has_error = False
            self._refresh_screen()
        except GammaDomainError:
            # x was zero or a negative integer (a true pole of Gamma).
            self._show_error(_format_x(x), "Undefined here")
        except GammaOverflowError:
            # The true result would exceed a 64-bit float's range.
            self._show_error(_format_x(x), "Out of range")
        # pylint: disable=broad-exception-caught
        # Intentionally broad: this is a GUI event handler's last line of
        # defense. The two specific domain exceptions above are handled
        # first; this final catch exists only so that any truly unforeseen
        # error surfaces as a message on the calculator screen instead of
        # crashing the whole application mid-demo. Narrowing this to a
        # named exception type isn't possible by definition, since the
        # whole point is to catch what we didn't anticipate.
        except Exception:  # pragma: no cover - unforeseen error safety net
            self._show_error(_format_x(x), "Error")

    def _show_error(self, x_label, message):
        """Display an error message on the screen in place of a result,
        keeping the history line so the user can see which input caused it."""
        self.has_error = True
        self.just_evaluated = True  # next digit should start a fresh entry
        self.history_var.set(f"\u0393({x_label})")
        self.current_entry = message
        self._refresh_screen()

    def _refresh_screen(self):
        """Push the current state onto the visible display, adjusting both
        color (green/white for a result, muted rose for an error) and font
        size (large for short numeric results, smaller for longer error
        text so it never wraps across multiple lines)."""
        self.display_var.set(self.current_entry)
        self.display_label.configure(
            fg=SCREEN_ERR if self.has_error else SCREEN_FG
        )

        # Adaptive font size: short numeric results get the big calculator
        # look; longer error text shrinks to fit on one line instead of
        # wrapping across the screen.
        length = len(self.current_entry)
        if length <= 10:
            size = 30
        elif length <= 16:
            size = 22
        else:
            size = 16
        self.display_label.configure(font=(DISPLAY_FONT_FAMILY, size, "bold"))


def _format_x(x):
    """
    Display integers without a trailing .0 (e.g. Gamma(5) not Gamma(5.0)).

    Args:
        x (float): the value to format.
    Returns:
        str: "5" for whole numbers, otherwise the plain string form of x.
    """
    if x == int(x):
        return str(int(x))
    return str(x)


if __name__ == "__main__":
    app = GammaApp()
    app.mainloop()